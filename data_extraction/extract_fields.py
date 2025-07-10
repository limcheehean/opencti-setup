from glob import glob
from json import load, dump
from os import path


def get_all_keys(obj, parent_key=''):
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{parent_key}.{k}" if parent_key else k
            keys.add(full_key)
            keys.update(get_all_keys(v, full_key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            full_key = f"{parent_key}"
            keys.update(get_all_keys(item, full_key))
    return keys


def extract_fields():
    files = glob("data/*/*.json", recursive=True)
    entity_types = set()
    for _, file in enumerate(files):
        print(f"Processing {_} of {len(files)} files")
        with open(file, "r") as f:
            entities = load(f)
            for entity in entities:
                entity_types.add(entity.get("entity_type"))

    with open("entity_types.json", "w") as f:
        dump(list(entity_types), f, indent=2)


if __name__ == "__main__":
    extract_fields()

