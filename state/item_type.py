import json

from state.config import AccountConfig, UploadConfig, TranslationConfig, DownloadConfig


def load_json_file(file, name=None):
    with open(file, encoding="utf-8") as file:
        loaded = json.load(file)
        if name == "default":
            name = loaded["default"]
        return loaded[name] if name else loaded


class ItemType:
    def __init__(self):
        self.accounts = AccountConfig()
        self.upload = UploadConfig()
        self.translation = TranslationConfig()
        self.download = DownloadConfig()
        self.accounts.load(load_json_file("user/accounts.json"))
        self.get_info()

    def get_info(self, name="default"):
        self.upload.load(load_json_file("user/upload.json", name))
        self.translation.load(load_json_file("user/translation.json", name))
        self.download.load(load_json_file("user/download.json"))
