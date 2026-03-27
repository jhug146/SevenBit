from state.item import Item


class ItemList:
    def __init__(self):
        self.items = None

    def load(self, headers, rows):
        item_dicts = [{} for _ in range(len(rows))]
        for i, row in enumerate(rows):
            for j, header in enumerate(headers):
                if header:
                    item_dicts[i][header] = row[j]
        self.items = [Item.from_dict(d) for d in item_dicts]
