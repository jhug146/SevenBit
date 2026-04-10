from upload.upload import chunkstring
from upload.translation.item_generator import _in_to_cm, _remove_dupes


# --- chunkstring ---

def test_chunkstring_exact_fit():
    assert list(chunkstring("ABCDEFGHI", 9)) == ["ABCDEFGHI"]

def test_chunkstring_with_remainder():
    assert list(chunkstring("ABCDEFGHIJ", 9)) == ["ABCDEFGHI", "J"]

def test_chunkstring_empty():
    assert list(chunkstring("", 9)) == []


# --- _in_to_cm ---

def test_in_to_cm_basic():
    assert _in_to_cm("10") == "25"

def test_in_to_cm_jeans_size():
    assert _in_to_cm("32") == "80"

def test_in_to_cm_zero():
    assert _in_to_cm("0") == "0"


# --- _remove_dupes ---

def test_remove_dupes_exact_match():
    assert _remove_dupes("Blue Blue Jeans") == "Blue Jeans"

def test_remove_dupes_case_insensitive():
    assert _remove_dupes("Blue blue Jeans") == "Blue Jeans"

def test_remove_dupes_no_dupes():
    assert _remove_dupes("Blue Jeans") == "Blue Jeans"

def test_remove_dupes_empty():
    assert _remove_dupes("") == ""

def test_remove_dupes_trailing_dupe():
    assert _remove_dupes("Blue Jeans Blue") == "Blue Jeans"
