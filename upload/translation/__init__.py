from upload.models.item_batch import ItemBatch
from upload.translation.specifics_builder import SpecificsBuilder
from upload.translation.field_translator import FieldTranslator
from upload.translation.item_generator import ItemGenerator


class EbayTranslator:
    GOOGLE_TRANSLATE_CODES = (None, None, None, "fr", "de", "it", "es")

    def __init__(self, translation_config, upload_mode, accounts):
        self.translation_config = translation_config
        self.upload_mode = upload_mode
        self.builder = SpecificsBuilder(translation_config)
        self.field_translator = FieldTranslator(translation_config)
        self.generator = ItemGenerator(translation_config, accounts)

    def translate(self, items):
        enriched = self.builder.build(items)
        translated_items = []
        website_upload = self.upload_mode.any_website_enabled()

        for item_count, item in enumerate(enriched, 1):
            print(f"Translating {item_count} / {len(enriched)}")
            item_translation = []

            for i, gt_code in enumerate(self.GOOGLE_TRANSLATE_CODES):
                country_code = self.translation_config.country_codes[i]
                if (not self.upload_mode.upload_state[i] or not country_code) and ((not website_upload) or i != 1):
                    item_translation.append(None)
                    continue

                translated_dict = self.field_translator.translate(item, i, gt_code)
                result = self.generator.generate(translated_dict, i, gt_code, item)
                item_translation.append(result)

            translated_items.append(ItemBatch(item_translation))

        return translated_items
