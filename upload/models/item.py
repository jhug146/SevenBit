from __future__ import annotations
import re
from dataclasses import dataclass, field


_FIELD_MAP = {
    "Title":                      "title",
    "SKU":                        "sku",
    "Price":                      "price",
    "Path":                       "images",
    "eBay Description":           "html",
    "eBay Condition":             "ebay_condition",
}

_CONDITION_RE = re.compile(r"^Condition (\d+)$")


@dataclass
class Item:
    title: str = ""
    sku: str = ""
    price: str = ""
    images: str = ""
    html: str = ""
    ebay_condition: str = ""
    condition_description: str = ""
    conditions: list = field(default_factory=list)
    specifics: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        kwargs = {}
        specifics = {}
        numbered_conditions = {}
        for key, value in data.items():
            if key in _FIELD_MAP:
                kwargs[_FIELD_MAP[key]] = value
            elif m := _CONDITION_RE.match(key):
                numbered_conditions[int(m.group(1))] = value
            else:
                specifics[key] = value
        conditions = [numbered_conditions[n] for n in sorted(numbered_conditions)]
        return cls(**kwargs, conditions=conditions, specifics=specifics)

    def to_dict(self) -> dict:
        result = {
            "Title":            self.title,
            "SKU":              self.sku,
            "Price":            self.price,
            "Path":             self.images,
            "eBay Description": self.html,
            "eBay Condition":   self.ebay_condition,
        }
        for i, c in enumerate(self.conditions, start=1):
            result[f"Condition {i}"] = c
        result.update(self.specifics)
        return result

    def __getitem__(self, name: str) -> str:
        if name in _FIELD_MAP:
            return getattr(self, _FIELD_MAP[name])
        if m := _CONDITION_RE.match(name):
            i = int(m.group(1)) - 1
            return self.conditions[i] if i < len(self.conditions) else ""
        return self.specifics[name]

    def __setitem__(self, name: str, value: str):
        if name in _FIELD_MAP:
            setattr(self, _FIELD_MAP[name], value)
        elif m := _CONDITION_RE.match(name):
            i = int(m.group(1)) - 1
            while len(self.conditions) <= i:
                self.conditions.append("")
            self.conditions[i] = value
        else:
            self.specifics[name] = value

    def keys(self):
        condition_keys = [f"Condition {i+1}" for i in range(len(self.conditions))]
        return list(_FIELD_MAP.keys()) + condition_keys + list(self.specifics.keys())

    def __len__(self):
        return len(_FIELD_MAP) + len(self.conditions) + len(self.specifics)
