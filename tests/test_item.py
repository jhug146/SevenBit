import pytest
from upload.models.item import Item


SAMPLE_DICT = {
    "Title": "Blue Slim Jeans",
    "SKU": "SK-000001",
    "Price": "9.99",
    "Path": "/images/test.jpg",
    "eBay Description": "<p>desc</p>",
    "eBay Condition": "Used",
    "Condition 1": "Good",
    "Condition 2": "No rips",
    "IS_Size": "32",
    "IS_Department": "Men",
}


# --- from_dict ---

def test_from_dict_maps_standard_fields():
    item = Item.from_dict(SAMPLE_DICT)
    assert item.title == "Blue Slim Jeans"
    assert item.sku == "SK-000001"
    assert item.price == "9.99"

def test_from_dict_parses_conditions_in_order():
    item = Item.from_dict(SAMPLE_DICT)
    assert item.conditions == ["Good", "No rips"]

def test_from_dict_collects_specifics():
    item = Item.from_dict(SAMPLE_DICT)
    assert item.specifics == {"IS_Size": "32", "IS_Department": "Men"}

def test_from_dict_out_of_order_conditions():
    data = {"Condition 3": "Faded", "Condition 1": "Good"}
    item = Item.from_dict(data)
    assert item.conditions == ["Good", "Faded"]


# --- to_dict ---

def test_to_dict_roundtrip_standard_fields():
    item = Item.from_dict(SAMPLE_DICT)
    result = item.to_dict()
    assert result["Title"] == "Blue Slim Jeans"
    assert result["SKU"] == "SK-000001"

def test_to_dict_roundtrip_conditions():
    item = Item.from_dict(SAMPLE_DICT)
    result = item.to_dict()
    assert result["Condition 1"] == "Good"
    assert result["Condition 2"] == "No rips"

def test_to_dict_roundtrip_specifics():
    item = Item.from_dict(SAMPLE_DICT)
    result = item.to_dict()
    assert result["IS_Size"] == "32"


# --- __getitem__ ---

def test_getitem_mapped_field():
    item = Item.from_dict(SAMPLE_DICT)
    assert item["Title"] == "Blue Slim Jeans"

def test_getitem_condition():
    item = Item.from_dict(SAMPLE_DICT)
    assert item["Condition 1"] == "Good"

def test_getitem_condition_out_of_bounds_returns_empty():
    item = Item.from_dict(SAMPLE_DICT)
    assert item["Condition 99"] == ""

def test_getitem_specific():
    item = Item.from_dict(SAMPLE_DICT)
    assert item["IS_Size"] == "32"


# --- __setitem__ ---

def test_setitem_mapped_field():
    item = Item.from_dict(SAMPLE_DICT)
    item["Title"] = "Red Jeans"
    assert item.title == "Red Jeans"

def test_setitem_condition():
    item = Item.from_dict(SAMPLE_DICT)
    item["Condition 1"] = "Worn"
    assert item.conditions[0] == "Worn"

def test_setitem_sparse_condition_extends_list():
    item = Item.from_dict(SAMPLE_DICT)
    item["Condition 5"] = "Faded"
    assert len(item.conditions) == 5
    assert item.conditions[4] == "Faded"

def test_setitem_specific():
    item = Item.from_dict(SAMPLE_DICT)
    item["IS_Color"] = "Blue"
    assert item.specifics["IS_Color"] == "Blue"
