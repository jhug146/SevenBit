from dataclasses import dataclass, field


_FIELD_MAP = {
    "Title":                      "title",
    "SKU":                        "sku",
    "Fixed Price eBay":           "price",
    "Path":                       "path",
    "eBay Description":           "ebay_description",
    "eBay Condition Description": "condition_description",
    "eBay Condition":             "ebay_condition",
    "eBay Category1ID":           "category_id",
    "eBay Store Category1ID":     "store_category_id",
    "Condition 1":                "condition_1",
    "Condition 2":                "condition_2",
    "Condition 4 (Free Text)":    "condition_4",
}


@dataclass
class Item:
    title: str = ""
    sku: str = ""
    price: str = ""
    path: str = ""
    ebay_description: str = ""
    condition_description: str = ""
    ebay_condition: str = ""
    category_id: str = ""
    store_category_id: str = ""
    condition_1: str = ""
    condition_2: str = ""
    condition_4: str = ""
    specifics: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        kwargs = {}
        specifics = {}
        for key, value in data.items():
            if key in _FIELD_MAP:
                kwargs[_FIELD_MAP[key]] = value
            else:
                specifics[key] = value
        return cls(**kwargs, specifics=specifics)

    def to_dict(self) -> dict:
        result = {
            "Title":                      self.title,
            "SKU":                        self.sku,
            "Fixed Price eBay":           self.price,
            "Path":                       self.path,
            "eBay Description":           self.ebay_description,
            "eBay Condition Description": self.condition_description,
            "eBay Condition":             self.ebay_condition,
            "eBay Category1ID":           self.category_id,
            "eBay Store Category1ID":     self.store_category_id,
            "Condition 1":                self.condition_1,
            "Condition 2":                self.condition_2,
            "Condition 4 (Free Text)":    self.condition_4,
        }
        result.update(self.specifics)
        return result

    def __getitem__(self, name: str) -> str:
        if name in _FIELD_MAP:
            return getattr(self, _FIELD_MAP[name])
        return self.specifics[name]

    def __setitem__(self, name: str, value: str):
        if name in _FIELD_MAP:
            setattr(self, _FIELD_MAP[name], value)
        else:
            self.specifics[name] = value

    def keys(self):
        return list(_FIELD_MAP.keys()) + list(self.specifics.keys())

    def __len__(self):
        return len(_FIELD_MAP) + len(self.specifics)
