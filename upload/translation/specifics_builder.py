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
            elif "default" in spec:
                lookup[field] = spec["default"]
        ranged = {}
        for field, spec in self.translation_config.range_specifics.items():
            value = float(base_dict.get(spec["value_field"], 0))
            condition = base_dict.get(spec["condition_field"], "")
            for entry in spec["ranges"].get(condition, []):
                if "max" not in entry or value < entry["max"]:
                    ranged[field] = entry["value"]
                    break
        contains = {}
        for field, spec in self.translation_config.contains_specifics.items():
            source = base_dict.get(spec["source"], "").lower()
            for case in spec["cases"]:
                if case["contains"].lower() in source:
                    contains[field] = case["value"]
                    break
        equality = {
            k: (v["if_equal"] if all(str(base_dict.get(a, '')) == str(base_dict.get(b, '')) for a, b in v["pairs"]) else v["else"])
            for k, v in self.translation_config.equality_specifics.items()
        }
        merged = {**base_dict, **computed, **conditional, **lookup, **ranged, **equality, **contains, **self.translation_config.default_specifics}
        item = Item.from_dict(merged)
        item.description = self._build_vinted_description(merged)
        return item

    def _build_vinted_description(self, d):
        spec = self.translation_config.vinted_description
        if not spec:
            return ""
        sections = []
        for section in spec:
            lines = [section["heading"] + ":"]
            for p in section.get("preamble", []):
                lines.append(p)
            if section.get("conditions"):
                i = 1
                while True:
                    val = d.get(f"Condition {i}", "")
                    if not val:
                        break
                    lines.append(val)
                    i += 1
            for field in section.get("fields", []):
                val = d.get(field["source"], "")
                if val:
                    lines.append(f"{field['label']}: {val}{field.get('suffix', '')}")
            sections.append("\n".join(lines))
        return "\n\n".join(sections)
