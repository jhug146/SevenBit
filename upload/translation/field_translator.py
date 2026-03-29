import re
import time

from deep_translator import GoogleTranslator


class FieldTranslator:
    def __init__(self, translation_config):
        self.translation_config = translation_config
        self.translators = (
            GoogleTranslator(source="auto", target="french"),
            GoogleTranslator(source="auto", target="german"),
            GoogleTranslator(source="auto", target="italian"),
            GoogleTranslator(source="auto", target="spanish")
        )

    def translate(self, item, country_index, gt_code):
        translation_data = (
            self.translation_config.per_country_translations[country_index]
            if self.translation_config.per_country_translations
            else None
        )
        if not translation_data:
            return item.to_dict()

        country_code = self.translation_config.country_codes[country_index]
        no_long_text_translation = self.translation_config.no_long_text_translation
        result = {}

        for header, detail in item.to_dict().items():
            detail_add = detail
            if header in translation_data:
                for key, value in translation_data[header].items():
                    if key == "":
                        if detail_add == "":
                            detail_add = value
                    else:
                        detail_add = re.sub(key, value, detail_add, flags=re.IGNORECASE)

            is_condition = bool(re.match(r"^Condition \d+$", header))
            if is_condition or header in self.translation_config.google_translate_fields:
                if (country_code in no_long_text_translation) or (not gt_code) or (not detail_add.strip()):
                    result[header] = detail_add
                    continue

                cond_trans = self.translation_config.condition_translation.get(header, {})
                for key, value in cond_trans.items():
                    if detail_add == key:
                        detail_add = value[country_index - 3]
                        break
                else:
                    attempts = 0
                    while attempts < 4:
                        try:
                            detail_add = self.translators[country_index - 3].translate_batch([detail])
                            if not type(detail_add) is str:
                                detail_add = detail_add[0]
                            break
                        except AttributeError as error:
                            print(error)
                        attempts += 1
                        time.sleep(0.5)
                        if attempts >= 3:
                            print("GT Error")

            result[header] = detail_add

        return result
