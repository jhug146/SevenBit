from state._json import load_json_file


class ItemType:
    def __init__(self):
        self.get_info()

    def get_info(self, name="default"):
        self.translation_data = load_json_file("user/translation.json", name)
        self.upload_data = load_json_file("user/upload.json", name)
        self.download_data = load_json_file("user/download.json")

    def pass_upload(self, upload_mode):
        self.upload_mode = upload_mode
