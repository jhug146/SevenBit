from state.config.base_config import BaseConfig


class UploadConfig(BaseConfig):
    def load(self, data):
        self._data = data
        self._validate()

    @property
    def name(self): return self._data["name"]

    @property
    def upload_to(self): return self._data["upload_to"]

    @property
    def max_title_length(self): return self._data["upload_requirements"]["max_title_length"]

    @property
    def max_price(self): return self._data["upload_requirements"]["max_price"]

    @property
    def min_price(self): return self._data["upload_requirements"]["min_price"]

    @property
    def picture_data(self): return self._data["pictureData"]

    @property
    def website_url(self): return self._data["website"]["url"]

    @property
    def website_images(self): return self._data["website"]["images"]

    @property
    def website_item(self): return self._data["website"]["item"]

    @property
    def condition_opening(self): return self._data["condition_opening"]

    @property
    def condition_closing(self): return self._data["condition_closing"]

    @property
    def display_order(self): return self._data["display_order"]

    @property
    def translate_headers(self): return self._data["translate_headers"]

    @property
    def is_names(self): return self._data["is_names"]

    @property
    def country(self): return self._data["user_info"]["country"]

    @property
    def county(self): return self._data["user_info"]["county"]

    @property
    def postcode(self): return self._data["user_info"]["postcode"]

    @property
    def max_dispatch_time(self): return self._data["user_info"]["max_dispatch_time"]

    @property
    def field_mapping(self): return self._data["field_mapping"]
