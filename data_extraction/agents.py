from collections import defaultdict
from json import dumps, loads
from os import getenv
from textwrap import dedent
from typing import Union

from elasticsearch.dsl import Search
from elasticsearch.helpers import scan

from clients import get_model, get_elasticsearch

model_name = "deepseek-chat"
es_client = get_elasticsearch()
index_name = getenv("ELASTICSEARCH_INDEX")
excluded_fields = ["embedding"]


def query_es(search, first=False) -> Union[dict, list, None]:
    result = search.source(excludes=excluded_fields).execute()
    # hits = [{**hit.meta.to_dict(), **hit.to_dict()} for hit in result.hits]
    hits = [{"_id": hit.meta.id, **hit.to_dict()} for hit in result.hits]
    if first:
        return hits[0] if hits else None
    return hits


def group_entities(entities):
    grouped_entities = defaultdict(list)
    for entity in entities:
        grouped_entities[entity.get("entity_type")].append(entity)
    return dict(grouped_entities)


def convert_to_table(entities):
    keys = []
    for entity in entities:
        for key in entity.keys():
            if key not in keys:
                keys.append(key)
    print(keys)
    return ""


def search_data(query, entity_type, start_date=None, end_date=None):
    # Build filter and query
    search = Search(using=es_client, index=index_name).query("multi_match", query=query, fields=["name", "aliases", "description"]).filter("terms", **{"entity_type.keyword": entity_type})[:1000]
    if start_date:
        search = search.filter("range", **{"created": {"gte": start_date}})
    if end_date:
        search = search.filter("range", **{"created": {"lte": end_date}})
    entities = query_es(search)
    print(f"{len(entities)} entities found")

    if not entities:
        return "No entities found, you may want to try a different query, entity type or date range."

    # Find embedded relationship and entity ids
    entity_ids = [entity.get("id") for entity in entities]
    relationship_ids = set()
    related_entity_ids = set()
    for entity in entities:
        for obj in entity.get("objects", []):
            (relationship_ids if "basic-relationship" in obj.get("parent_types") else related_entity_ids).add(obj.get("id"))

    # Find external relationships
    relationships = query_es(Search(using=es_client, index=index_name).query("bool", should=[
        {"terms": {"from.id.keyword": entity_ids}},
        {"terms": {"to.id.keyword": entity_ids}},
        {"terms": {"id.keyword": relationship_ids}}
    ], minimum_should_match=1)[:1000])
    print(f"{len(relationships)} relationships found")

    # Get related entities
    entity_fields_excluded = ["standard_id", "parent_types", "createdBy", "objectMarking", "objectLabel", "objectMarkingIds", "objectLabelIds", "externalReferencesIds", "killChainPhases"]
    related_entity_ids.update({ids for relationship in relationships for ids in (relationship.get("from").get("id"), relationship.get("to").get("id"))})
    related_entities = query_es(Search(using=es_client, index=index_name).query("terms", **{"id.keyword": related_entity_ids})[:1000])
    related_entities = [{key: value for key, value in entity.items() if key not in entity_fields_excluded} for entity in related_entities if entity.get("id") not in entity_ids]
    print(f"{len(related_entities)} related entities found\n")

    message = ""
    for entity_type, type_entities in group_entities(entities).items():
        message += f"{len(type_entities)} entities of type {entity_type} found:\n{convert_to_table(type_entities)}\n"
        # for entity in type_entities:
        #     message += f"{entity}\n"
        # message += "\n"

    for entity_type, type_entities in group_entities(related_entities).items():
        message += f"{len(type_entities)} related entities of type {entity_type} found:{convert_to_table(type_entities)}\n"
        # for entity in type_entities:
        #     message += f"{entity}\n"
        # message += "\n"


    # Group by entity type
    # entity_types = {entity.get("entity_type") for entity in entities}
    # print(entity_types)
    # for entity_type in entity_types:
    #     print(entity_type)
    #     for entity in entities:
    #         if entity.get("entity_type") == entity_type:
    #             print(entity)



    # relationships = [
    #     {
    #         "relationship_type": relationship.get("entity_type"),
    #         "from": relationship.get("from").get("id"),
    #         "to": relationship.get("to").get("id")
    #     }
    #     for relationship in relationships
    # ]
    # Summarise
    # results = [generate_summary(result) for result in results]
    # print(dumps([loads(result) for result in results], indent=2))

    print(message)
    return message


# def get_entity(entity_id):
#     # Find entity
#     entity = query_es(Search(using=es_client, index=index_name).query("term", **{"id.keyword": entity_id})[:1], first=True)
#     if not entity:
#         return None
#     entity_summary = generate_summary(entity)
#
#     # Find relationships
#     relationships = query_es(Search(using=es_client, index=index_name).query("bool", should=[
#         {"term": {"from.id.keyword": entity_id}},
#         {"term": {"to.id.keyword": entity_id}}
#     ], minimum_should_match=1)[:1000])
#     related_entity_ids = [from_id if ((from_id := relationship.get("from").get("id")) != entity.get("id")) else relationship.get("to").get("id") for relationship in relationships]
#
#     # Find related entities
#     related_entities = query_es(Search(using=es_client, index=index_name).query("terms", **{"id.keyword": related_entity_ids})[:1000])
#     for related_entity in related_entities:
#         relationship = next(relationship for relationship in relationships if related_entity.get("id") in [relationship.get("from").get("id"), relationship.get("to").get("id")])
#         related_entity.update(**{
#             "summary": generate_summary(related_entity),
#             "relationship_type": relationship.get("entity_type"),
#             "relationship_direction": "from" if relationship.get("from").get("id") == related_entity.get("id") else "to"
#         })
#
#     message = f"""
# Below is the summary of the entity you searched for ({entity_id})
# {entity_summary}
#
# Below are the entities that are related to the entity.\n\n"""
#
#     for related_entity in related_entities:
#         if related_entity.get('entity_type') == "report":
#             print("YAY")
#             print(related_entity)
#         message += f"{related_entity.get('id') if related_entity.get('relationship_direction') == "from" else entity_id} {related_entity.get('relationship_type')} to {entity_id if related_entity.get('relationship_direction') == "to" else entity_id}\n"
#         message += f"Summary of {related_entity.get('id')}:\n{related_entity.get('summary').replace('\n', ' ')}\n\n"
#
#     print(message)
#     return message


def generate_summary(entity):
    if (summary := entity.get("summary")) and summary.startswith("{"):
        return summary
    print(f"[SUMMARISE] {entity.get("standard_id")}")
    prompt = f"""
    Summarise this object.
    - The aim is to provide relevant information to be analysed for threat intelligence purposes.
    - Remove all fields that are irrelevant, empty or not useful for threat intelligence analysis.
    - Flatten objectMarking and objectLabel into a list of strings.
    
    {entity}
    
    Return ONLY the json without any other information.
    """
    client = get_model(model_name)
    response = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
    summary = response.choices[0].message.content

    # Save into elasticsearch
    es_client.update(index=index_name, id=entity.get("_id"), body={"doc": {"summary": summary}})

    print(f"[SUMMARISE RESULT] {summary.replace('\n', ' ')}")
    return summary


if __name__ == "__main__":
    search_data("danabot", ['Report', 'Indicator', 'Campaign'])


