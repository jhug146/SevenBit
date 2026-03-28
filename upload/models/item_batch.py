from __future__ import annotations
from upload.models.item import Item


class ItemBatch:
    """A translated item batch — one Item per regional site, some may be None.

    Index 0 = US, 1 = UK, 2 = Australia, 3 = France, 4 = Germany, 5 = Italy, 6 = Spain.
    The UK item (index 1) is used as the canonical English version; if the batch has
    only one item (untranslated), that item is used instead.
    """

    def __init__(self, items: list):
        self._items = items

    @property
    def default(self) -> Item:
        """The English (UK) item, or the only item if untranslated."""
        return self._items[1] if len(self._items) > 1 else self._items[0]

    def __getitem__(self, site_num: int) -> Item:
        return self._items[site_num]

    @property
    def sku(self) -> str:
        return self.default.sku

    @property
    def title(self) -> str:
        return self.default.title

    @property
    def images(self) -> str:
        return self.default.images

    @property
    def price(self) -> str:
        return self.default.price

    def __len__(self):
        return len(self._items)
