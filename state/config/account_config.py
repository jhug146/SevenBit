from state.config.base_config import BaseConfig


class AccountConfig(BaseConfig):
    def load(self, data):
        self._data = data
        self._current = data[data["default"]]
        self._validate()

    @property
    def name(self): return self._current["name"]

    @property
    def appid(self): return self._current["credentials"]["appid"]

    @property
    def certid(self): return self._current["credentials"]["certid"]

    @property
    def devid(self): return self._current["credentials"]["devid"]

    @property
    def token(self): return self._current["credentials"]["token"]

    @property
    def allowed_destinations(self): return self._current.get("allowed_destinations")

    @property
    def build_condition(self): return self._current["build_condition"]

    @property
    def website_url(self): return self._current["website"]["url"]

    @property
    def website_item(self): return self._current["website"]["item"]

    @property
    def website_images(self): return self._current["website"]["images"]

    def policies(self, item_type_name): return self._current["policies"][item_type_name]

    def set_upload_attr(self, upload):
        self.upload = upload

    def switch_account(self, name):
        try:
            self._current = self._data[name]
            self.upload.update_connections()
            return True
        except (ValueError, KeyError):
            return False
