from dataclasses import dataclass


@dataclass
class UploadResult:
    status: str       # "Success", "Warning", or "Failure"
    sort_key: int     # controls ordering of results: eBay site_num (0-6), other destinations (7+)
    message: str = ""


@dataclass
class ImageUploadResult:
    success: bool
    pic_id: int       # original index, used to restore order after parallel upload
    url: str = ""
