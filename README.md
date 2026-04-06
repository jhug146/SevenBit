# SevenBit
Upload, translation and download tool for eBay's REST API.

## SKU Wash Codes

SKUs (`SK-NNNNNN`) are obfuscated into 5-character hex wash codes for external use. Use these Excel formulas to convert between them.

### Encode — `SK-NNNNNN` to wash code

> Assumes the SKU is in cell **A1**

```excel
=DEC2HEX(MOD(234571*VALUE(MID(A1,4,100))+517834,1000000),5)
```

### Decode — wash code to `SK-NNNNNN`

> Assumes the wash code is in cell **B1**

```excel
="SK-"&TEXT(MOD(167331*(HEX2DEC(B1)-517834),1000000),"000000")
```

| Input | Output |
|-------|--------|
| `SK-000001` | `B7B15` |
| `B7B15` | `SK-000001` |

---

## Setup

```bash
pip install -r requirements.txt
python __main__.py
```

