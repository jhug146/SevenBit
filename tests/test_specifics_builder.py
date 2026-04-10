from types import SimpleNamespace

from upload.models.item import Item
from upload.translation.specifics_builder import SpecificsBuilder


def make_config(computed=None, conditional=None, lookup=None,
                range_specifics=None, contains=None, equality=None,
                default=None, vinted=None):
    return SimpleNamespace(
        computed_specifics=computed or {},
        conditional_specifics=conditional or {},
        lookup_specifics=lookup or {},
        range_specifics=range_specifics or {},
        contains_specifics=contains or {},
        equality_specifics=equality or {},
        default_specifics=default or {},
        vinted_description=vinted or [],
    )


def make_item(**specifics):
    data = {
        "Title": "Blue Slim Jeans",
        "SKU": "SK-000001",
        "Price": "9.99",
        "Path": "",
        "eBay Description": "",
        "eBay Condition": "",
        **specifics,
    }
    return Item.from_dict(data)


def build_one(config, item):
    return SpecificsBuilder(config).build([item])[0]


# --- computed ---

def test_computed_substitution():
    config = make_config(computed={"IS_Label": "{Title} ({IS_Size})"})
    result = build_one(config, make_item(**{"IS_Size": "32"}))
    assert result["IS_Label"] == "Blue Slim Jeans (32)"

def test_computed_missing_field_renders_empty():
    config = make_config(computed={"IS_X": "{NonExistent}"})
    result = build_one(config, make_item())
    assert result["IS_X"] == ""


# --- conditional ---

def test_conditional_then_branch():
    config = make_config(conditional={
        "IS_Region": {"source": "IS_Department", "if_equals": "Men", "then": "US", "else": "UK"}
    })
    result = build_one(config, make_item(**{"IS_Department": "Men"}))
    assert result["IS_Region"] == "US"

def test_conditional_else_branch():
    config = make_config(conditional={
        "IS_Region": {"source": "IS_Department", "if_equals": "Men", "then": "US", "else": "UK"}
    })
    result = build_one(config, make_item(**{"IS_Department": "Women"}))
    assert result["IS_Region"] == "UK"


# --- lookup ---

def test_lookup_two_level_found():
    config = make_config(lookup={
        "IS_Label": {
            "fields": ["IS_Department", "IS_Size"],
            "map": {"Men": {"32": "W32 Mens"}},
        }
    })
    result = build_one(config, make_item(**{"IS_Department": "Men", "IS_Size": "32"}))
    assert result["IS_Label"] == "W32 Mens"

def test_lookup_not_found_uses_default():
    config = make_config(lookup={
        "IS_Label": {
            "fields": ["IS_Department"],
            "map": {"Men": "Mens"},
            "default": "Unknown",
        }
    })
    result = build_one(config, make_item(**{"IS_Department": "Kids"}))
    assert result["IS_Label"] == "Unknown"

def test_lookup_not_found_no_default_omits_field():
    config = make_config(lookup={
        "IS_Label": {
            "fields": ["IS_Department"],
            "map": {"Men": "Mens"},
        }
    })
    result = build_one(config, make_item(**{"IS_Department": "Kids"}))
    assert "IS_Label" not in result.to_dict()


# --- range ---

def test_range_below_max():
    config = make_config(range_specifics={
        "IS_Fit": {
            "value_field": "IS_Waist",
            "condition_field": "IS_Department",
            "ranges": {"Men": [{"max": 32, "value": "Slim"}, {"value": "Regular"}]},
        }
    })
    result = build_one(config, make_item(**{"IS_Waist": "30", "IS_Department": "Men"}))
    assert result["IS_Fit"] == "Slim"

def test_range_above_max_falls_to_unbounded_entry():
    config = make_config(range_specifics={
        "IS_Fit": {
            "value_field": "IS_Waist",
            "condition_field": "IS_Department",
            "ranges": {"Men": [{"max": 32, "value": "Slim"}, {"value": "Regular"}]},
        }
    })
    result = build_one(config, make_item(**{"IS_Waist": "34", "IS_Department": "Men"}))
    assert result["IS_Fit"] == "Regular"

def test_range_unknown_condition_omits_field():
    config = make_config(range_specifics={
        "IS_Fit": {
            "value_field": "IS_Waist",
            "condition_field": "IS_Department",
            "ranges": {"Men": [{"value": "Regular"}]},
        }
    })
    result = build_one(config, make_item(**{"IS_Waist": "32", "IS_Department": "Women"}))
    assert "IS_Fit" not in result.to_dict()


# --- contains ---

def test_contains_first_match_wins():
    config = make_config(contains={
        "IS_Color": {
            "source": "Title",
            "cases": [{"contains": "blue", "value": "Blue"}, {"contains": "slim", "value": "Slim"}],
        }
    })
    result = build_one(config, make_item())  # Title = "Blue Slim Jeans"
    assert result["IS_Color"] == "Blue"

def test_contains_case_insensitive():
    config = make_config(contains={
        "IS_Color": {"source": "Title", "cases": [{"contains": "BLUE", "value": "Blue"}]}
    })
    result = build_one(config, make_item())
    assert result["IS_Color"] == "Blue"

def test_contains_no_match_omits_field():
    config = make_config(contains={
        "IS_Color": {"source": "Title", "cases": [{"contains": "red", "value": "Red"}]}
    })
    result = build_one(config, make_item())
    assert "IS_Color" not in result.to_dict()


# --- equality ---

def test_equality_all_pairs_match():
    config = make_config(equality={
        "IS_Square": {"pairs": [["IS_Width", "IS_Height"]], "if_equal": "Yes", "else": "No"}
    })
    result = build_one(config, make_item(**{"IS_Width": "32", "IS_Height": "32"}))
    assert result["IS_Square"] == "Yes"

def test_equality_pair_mismatch():
    config = make_config(equality={
        "IS_Square": {"pairs": [["IS_Width", "IS_Height"]], "if_equal": "Yes", "else": "No"}
    })
    result = build_one(config, make_item(**{"IS_Width": "32", "IS_Height": "30"}))
    assert result["IS_Square"] == "No"


# --- vinted description ---

def test_vinted_description_fields():
    config = make_config(vinted=[{
        "heading": "Details",
        "fields": [{"source": "IS_Size", "label": "Size", "suffix": " inches"}],
    }])
    result = build_one(config, make_item(**{"IS_Size": "32"}))
    assert result.description == "Details:\nSize: 32 inches"

def test_vinted_description_conditions():
    config = make_config(vinted=[{"heading": "Condition", "conditions": True}])
    item = Item.from_dict({
        "Title": "Jeans", "SKU": "SK-000001", "Price": "9.99",
        "Path": "", "eBay Description": "", "eBay Condition": "",
        "Condition 1": "Good", "Condition 2": "No rips",
    })
    result = build_one(config, item)
    assert "Good" in result.description
    assert "No rips" in result.description

def test_vinted_description_empty_when_no_config():
    config = make_config()
    result = build_one(config, make_item())
    assert result.description == ""

def test_vinted_description_multiple_sections_joined():
    config = make_config(vinted=[
        {"heading": "Section A", "fields": [{"source": "IS_Size", "label": "Size"}]},
        {"heading": "Section B", "fields": [{"source": "IS_Department", "label": "Dept"}]},
    ])
    result = build_one(config, make_item(**{"IS_Size": "32", "IS_Department": "Men"}))
    assert result.description == "Section A:\nSize: 32\n\nSection B:\nDept: Men"
