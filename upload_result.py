from dataclasses import dataclass, field


@dataclass
class UploadResult:
    status: str       # "Success", "Warning", or "Failure"
    sort_key: int     # controls ordering of results: eBay site_num (0-6), other destinations (7+)
    message: str = ""
