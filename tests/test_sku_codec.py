from upload.destinations.sku_codec import encode_sku, decode_sku


# Known value: SK-000001 → "B7B15"  (234571*1 + 517834 = 752405 = 0xB7B15)
def test_encode_known_value():
    assert encode_sku("SK-000001") == "B7B15"


def test_decode_known_value():
    assert decode_sku("B7B15") == "SK-000001"


def test_roundtrip_single():
    assert decode_sku(encode_sku("SK-123456")) == "SK-123456"


def test_roundtrip_zero():
    assert decode_sku(encode_sku("SK-000000")) == "SK-000000"


def test_roundtrip_max():
    assert decode_sku(encode_sku("SK-999999")) == "SK-999999"
