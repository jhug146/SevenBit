from dataclasses import dataclass
from enum import Enum


class UploadStatus(Enum):
    SUCCESS = "Success"
    WARNING = "Warning"
    FAILURE = "Failure"


@dataclass
class UploadResult:
    status: UploadStatus
    message: str = ""


@dataclass
class ImageUploadResult:
    status: UploadStatus
    pic_id: int       # original index, used to restore order after parallel upload
    url: str = ""
