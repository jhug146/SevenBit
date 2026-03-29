import re

from upload.models.item import Item


class SpecificsBuilder:
    def __init__(self, translation_config):
        self.translation_config = translation_config

    def build(self, items):
        return [self._build_item(item) for item in items]

    def _build_item(self, item):
        base_dict = item.to_dict()
        computed = {
            k: re.sub(r'\{([^}]+)\}', lambda m: str(base_dict.get(m.group(1), '')), v)
            for k, v in self.translation_config.computed_specifics.items()
        }
        conditional = {
            k: (v["then"] if base_dict.get(v["source"]) == v["if_equals"] else v["else"])
            for k, v in self.translation_config.conditional_specifics.items()
        }
        lookup = {}
        for field, spec in self.translation_config.lookup_specifics.items():
            node = spec["map"]
            for f in spec["fields"]:
                node = node.get(str(base_dict.get(f, '')))
                if node is None:
                    break
            if isinstance(node, str):
                lookup[field] = node
        return Item.from_dict({**base_dict, **computed, **conditional, **lookup, **self.translation_config.default_specifics})
