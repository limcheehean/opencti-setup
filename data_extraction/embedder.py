from json import dumps
from os import getenv
from time import perf_counter

from elasticsearch.helpers import scan, bulk

from clients import get_model, get_elasticsearch

client = get_elasticsearch()
model = get_model("all-MiniLM-L6-v2")
embedding_properties = {
    "embedding": {
        "type": "dense_vector",
        "dims": 384  # Replace with your embedding size
    }
}
batch_size = 100
index_name = getenv("ELASTICSEARCH_INDEX")


def create_index_and_mapping_if_not_exists(index, properties):
    # Create index with mappings if index does not exist
    if not client.indices.exists(index=index):
        client.indices.create(index=index, body={"mappings": {"properties": properties}})
        return

    # Add properties not already exist
    fields = properties.keys()
    existing_fields = client.indices.get_mapping(index=index).get(index).get("mappings").get("properties").keys()
    for field in fields:
        if field not in existing_fields:
            client.indices.put_mapping(index=index, body={"properties": {field: properties[field]}})


def calculate_time_left(start_time, embed_count, current_count, total_count):
    time_elapsed = perf_counter() - start_time
    seconds = int(time_elapsed / embed_count * (total_count - current_count))
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m {seconds % 60}s"


def generate_embeddings():
    total_count = client.count(index=index_name, body={"query": {"match_all": {}}})["count"]
    not_embedded_query = {"query": {"bool": {"must_not": {"exists": {"field": "embedding"}}}}}
    not_embedded_count = client.count(index=index_name, body=not_embedded_query)["count"]
    current_count = total_count - not_embedded_count
    embed_count = 0
    entities = scan(client, index=index_name, query=not_embedded_query)
    start_time = perf_counter()

    for entity in entities:
        embeddings = model.encode(dumps(entity, indent=2))
        client.update(index=index_name, id=entity.get("_id"), body={"doc": {"embedding": embeddings}})
        current_count += 1
        embed_count += 1
        print(f"Embedded {current_count} of {total_count} entities ({round(current_count / total_count * 100, 3)}%)")
        print(f"Estimated time left: {calculate_time_left(start_time, embed_count, current_count, total_count)}")


if __name__ == "__main__":
    create_index_and_mapping_if_not_exists(index_name, embedding_properties)
    # generate_embeddings()
