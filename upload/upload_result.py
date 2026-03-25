from dataclasses import dataclass
from enum import Enum


class UploadStatus(Enum):
    SUCCESS = "Success"
    WARNING = "Warning"
    FAILURE = "Failure"


@dataclass
class UploadResult:
    status: UploadStatus
    sort_key: int     # controls ordering of results: eBay site_num (0-6), other destinations (7+)
    message: str = ""


@dataclass
class ImageUploadResult:
    status: UploadStatus
    pic_id: int       # original index, used to restore order after parallel upload
    url: str = ""
