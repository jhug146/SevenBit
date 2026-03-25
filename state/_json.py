import json


def load_json_file(file, name=None):
    with open(file, encoding="utf-8") as file:
        loaded = json.load(file)
        if name == "default":
            name = loaded["default"]
        return loaded[name] if name else loaded
