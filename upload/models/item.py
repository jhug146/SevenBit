from dataclasses import dataclass, field


_FIELD_MAP = {
    "Title":                      "title",
    "SKU":                        "sku",
    "Fixed Price eBay":           "price",
    "Path":                       "images",
    "eBay Description":           "html",
    "eBay Condition":             "ebay_condition",
    "condition_opener":           "condition_opener",
    "eBay Condition Description": "condition_description_raw",
}

_CONDITION_KEYS = (
    "Condition 1",
    "Condition 2",
    "Condition 4 (Free Text)",
)


@dataclass
class Item:
    title: str = ""
    sku: str = ""
    price: str = ""
    images: str = ""
    html: str = ""
    ebay_condition: str = ""
    condition_opener: str = ""
    condition_description_raw: str = ""
    conditions: list = field(default_factory=list)
    specifics: dict = field(default_factory=dict)

    @property
    def condition_description(self) -> str:
        if self.condition_description_raw:
            return self.condition_description_raw
        parts = [c for c in self.conditions if c and c != " "]
        return self.condition_opener + " ••••• ".join(parts)

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        kwargs = {}
        specifics = {}
        conditions = ["", "", ""]
        for key, value in data.items():
            if key in _FIELD_MAP:
                kwargs[_FIELD_MAP[key]] = value
            elif key in _CONDITION_KEYS:
                conditions[_CONDITION_KEYS.index(key)] = value
            else:
                specifics[key] = value
        return cls(**kwargs, conditions=conditions, specifics=specifics)

    def to_dict(self) -> dict:
        conditions = self.conditions + [""] * (3 - len(self.conditions))
        result = {
            "Title":                      self.title,
            "SKU":                        self.sku,
            "Fixed Price eBay":           self.price,
            "Path":                       self.images,
            "eBay Description":           self.html,
            "eBay Condition":             self.ebay_condition,
            "Condition 1":                conditions[0],
            "Condition 2":                conditions[1],
            "Condition 4 (Free Text)":    conditions[2],
        }
        result.update(self.specifics)
        return result

    def __getitem__(self, name: str) -> str:
        if name in _FIELD_MAP:
            return getattr(self, _FIELD_MAP[name])
        if name in _CONDITION_KEYS:
            i = _CONDITION_KEYS.index(name)
            return self.conditions[i] if i < len(self.conditions) else ""
        return self.specifics[name]

    def __setitem__(self, name: str, value: str):
        if name in _FIELD_MAP:
            setattr(self, _FIELD_MAP[name], value)
        elif name in _CONDITION_KEYS:
            i = _CONDITION_KEYS.index(name)
            while len(self.conditions) <= i:
                self.conditions.append("")
            self.conditions[i] = value
        else:
            self.specifics[name] = value

    def keys(self):
        return list(_FIELD_MAP.keys()) + list(_CONDITION_KEYS) + list(self.specifics.keys())

    def __len__(self):
        return len(_FIELD_MAP) + len(_CONDITION_KEYS) + len(self.specifics)
