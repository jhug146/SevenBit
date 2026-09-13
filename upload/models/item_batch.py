from __future__ import annotations
from upload.models.item import Item


class ItemBatch:
    """A translated item batch — one Item per regional site, some may be None.

    Index 0 = US, 1 = UK, 2 = Australia, 3 = France, 4 = Germany, 5 = Italy, 6 = Spain.
    """

    def __init__(self, items: list, original: Item):
        self._items = items
        self.original = original

    def __getitem__(self, site_num: int) -> Item:
        return self._items[site_num]

    @property
    def sku(self) -> str:
        return self.original.sku

    @property
    def title(self) -> str:
        return self.original.title

    @property
    def images(self) -> str:
        return self.original.images

    @property
    def price(self) -> str:
        return self.original.price

    def __len__(self):
        return len(self._items)
