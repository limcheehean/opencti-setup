from json import load, dump
from os import listdir, getenv
from time import perf_counter

from elasticsearch.helpers import bulk

from clients import get_elasticsearch

client = get_elasticsearch()
data_folder = getenv("DATA_FOLDER")
index_name = getenv("ELASTICSEARCH_INDEX")


def get_files_info():
    files = []
    entity_types = sorted(listdir(data_folder))
    total_count = 0
    for entity_type in entity_types:
        for file in sorted(listdir(f"{data_folder}/{entity_type}")):
            total_count += int(file.split("_")[1])
            files.append(f"{entity_type}/{file}")
    return sorted(files), total_count


def get_current_progress():
    if "loader_progress.log" not in listdir():
        return [], 0
    with open("loader_progress.log.old", "r") as file:
        processed = load(file)
    count = 0
    for file in processed:
        count += int(file.split("/")[1].split("_")[1])
    return sorted(processed), count


def save_current_progress(processed):
    with open("loader_progress.log.old", "w") as file:
        dump(processed, file, indent=2)


def get_file_data(filename):
    with open(filename, "r") as file:
        return load(file)


def calculate_time_left(start_time, load_count, processed_count, total_count):
    time_elapsed = perf_counter() - start_time
    seconds = int(time_elapsed / load_count * (total_count - processed_count))
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m {seconds % 60}s"


def load_opencti_data():
    files, total_count = get_files_info()
    processed, processed_count = get_current_progress()
    load_count = 0
    start_time = perf_counter()

    for file in files:
        if file in processed:
            continue
        entities = get_file_data(f"{data_folder}/{file}")
        entities = [{**entity, "_index": index_name, "_id": entity.get("standard_id")} for entity in entities]

        # Load into elasticsearch
        success, errors = bulk(client, entities)
        if errors:
            print(f"Errors have occurred: {errors}")
            return

        processed_count += len(entities)
        load_count += len(entities)
        processed.append(file)
        save_current_progress(processed)

        print(f"Loaded {processed_count} of {total_count} entities ({round(processed_count / total_count * 100, 3)}%)")
        print(f"Estimated time left: {calculate_time_left(start_time, load_count, processed_count, total_count)}")


if __name__ == "__main__":
    load_opencti_data()
