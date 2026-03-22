from abc import ABC, abstractmethod


class Destination(ABC):
    """Interface for non-eBay upload destinations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier matching the OPTIONS key in UploadMode (e.g. 'SQL')."""
        ...

    @abstractmethod
    def upload_images(self, paths: str, sku: str, title: str, display) -> list | None:
        """Upload images. Returns list of hosted URLs, or None on failure."""
        ...

    @abstractmethod
    def upload_item(self, item: dict, display) -> str:
        """Upload item data. Returns a status string prefixed with a sort-key character."""
        ...
