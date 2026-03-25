from state.upload_config import UploadConfig
from state.translation_config import TranslationConfig
from state.download_config import DownloadConfig


class ItemType:
    def __init__(self):
        self.upload = UploadConfig()
        self.translation = TranslationConfig()
        self.download = DownloadConfig()
        self.get_info()

    def get_info(self, name="default"):
        self.upload.load(name)
        self.translation.load(name)
        self.download.load()
