_MOD   = 1_000_000
_A     = 234_571
_B     = 517_834
_A_INV = pow(_A, -1, _MOD)


def encode_sku(sku: str) -> str:
    """SK-123456  →  1AF3C  (5-char hex wash code)"""
    n = int(sku.split("-", 1)[-1])
    m = (_A * n + _B) % _MOD
    return format(m, "05X")


def decode_sku(hex_code: str) -> str:
    """1AF3C  →  SK-123456"""
    m = int(hex_code, 16)
    n = (_A_INV * (m - _B)) % _MOD
    return f"SK-{n:06d}"
