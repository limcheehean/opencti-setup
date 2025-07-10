from json import dumps, dump
from os import getenv, listdir, makedirs
from time import perf_counter

from dotenv import load_dotenv

from clients import get_opencti

load_dotenv()
client = get_opencti()
batch_size = 5000
report_batch_size = 100  # Custom batch size to prevent gateway timeout
data_folder = getenv("DATA_FOLDER")



def get_entity_types():
    excluded = ["capability", "connector", "group", "role", "user", "vocabulary", "opencti_stix_object_or_stix_relationship"]
    attributes = [attr for attr in dir(client) if "list" in dir(getattr(client, attr)) and attr not in excluded]
    entity_types = {}
    for attribute in attributes:
        result = getattr(client, attribute).list(first=0, withPagination=True, with_pagination=True)
        entity_count = result.get("pagination").get("globalCount")
        if entity_count > 0:
            entity_types[attribute] = entity_count
    print(dumps(entity_types, indent=2))
    return entity_types


def get_entity_progress(entity_type):
    makedirs(f"{data_folder}/{entity_type}", exist_ok=True)
    files = sorted(listdir(f"{data_folder}/{entity_type}"))
    file_count, entity_count, after = 0, 0, None
    for file in files:
        _, file_entity_count, after = file.strip(".json").split("_")
        file_count += 1
        entity_count += int(file_entity_count)
    return file_count, entity_count, after


def calculate_time_left(start_time, download_count, current_count, total_count):
    time_elapsed = perf_counter() - start_time
    seconds = int(time_elapsed / download_count * (total_count - current_count))
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m {seconds % 60}s"


def download_opencti_data():
    entity_types = get_entity_types()
    total_count = sum(entity_types.values())    # Number of entries in opencti
    current_count = 0                           # Number of entries on disk
    download_count = 0                          # Number of entries downloaded in current run
    start_time = perf_counter()

    for entity_type, entity_total_count in entity_types.items():
        print(f"Retrieving {entity_type} ({entity_total_count})")
        file_count, entity_count, after = get_entity_progress(entity_type)
        current_count += entity_count

        # All entities of type already downloaded
        if entity_count >= entity_total_count:
            continue

        while True:
            first = report_batch_size if entity_type == "report" else batch_size
            result = getattr(client, entity_type).list(first=first, after=after, withPagination=True, with_pagination=True)
            entities = result.get("entities")
            if not entities:
                break
            after = result.get("pagination").get("endCursor")
            file_count += 1
            current_count += len(entities)
            download_count += len(entities)
            with open(f"{data_folder}/{entity_type}/{file_count:04}_{len(entities)}_{after}.json", "w") as file:
                dump(entities, file, indent=2)
            print(f"Retrieved {current_count} of {total_count} entities ({round(current_count / total_count * 100, 3)}%)")
            print(f"Estimated time left: {calculate_time_left(start_time, download_count, current_count, total_count)}")


if __name__ == "__main__":
    download_opencti_data()
