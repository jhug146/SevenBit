from state.config.base_config import BaseConfig


class DownloadConfig(BaseConfig):
    def load(self, data):
        self._data = data
        self._validate()

    @property
    def headers(self): return self._data["headers"]

    @property
    def set_values(self): return self._data["set_values"]

    @property
    def non_is_values(self): return self._data["non_is_values"]

    @property
    def is_values(self): return self._data["is_values"]

    @property
    def substrings(self): return self._data["substrings"]

    @property
    def save_folder(self): return self._data["save_folder"]
