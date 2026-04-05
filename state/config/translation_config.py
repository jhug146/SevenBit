from state.config.base_config import BaseConfig


class TranslationConfig(BaseConfig):
    def load(self, data):
        self._data = data
        self._validate()

    @property
    def country_codes(self): return self._data["country_codes"]

    @property
    def per_country_translations(self): return self._data["translation_data"]

    @property
    def google_translate_fields(self): return self._data["google_translate_fields"]

    @property
    def condition_translation(self): return self._data["condition_translation"]

    @property
    def condition_openers(self): return self._data["condition_openers"]

    @property
    def currency_codes(self): return self._data["currency_codes"]

    @property
    def no_long_text_translation(self): return self._data.get("no_long_text_translation")

    @property
    def translation_dupes(self): return self._data["translation_dupes"]

    @property
    def title_ignore(self): return self._data["title_ignore"]

    @property
    def title_fixing_data(self): return self._data["title_fixing_data"]

    @property
    def title_order(self): return self._data["title_order"]

    @property
    def category_specific_translations(self): return self._data["category_specific_translations"]

    @property
    def html(self): return self._data["html"]

    @property
    def computed_specifics(self): return self._data.get("computed_specifics", {})

    @property
    def lookup_specifics(self): return self._data.get("lookup_specifics", {})

    @property
    def conditional_specifics(self): return self._data.get("conditional_specifics", {})

    @property
    def range_specifics(self): return self._data.get("range_specifics", {})

    @property
    def equality_specifics(self): return self._data.get("equality_specifics", {})

    @property
    def contains_specifics(self): return self._data.get("contains_specifics", {})

    @property
    def default_specifics(self): return self._data.get("default_specifics", {})

    @property
    def vinted_description(self): return self._data.get("vinted_description")

    @property
    def leave_html(self): return self._data.get("leave_html")
