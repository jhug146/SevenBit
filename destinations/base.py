from abc import ABC, abstractmethod


class Destination(ABC):
    """Interface for non-eBay upload destinations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used as the toggle key (e.g. 'SQL')."""
        ...

    @property
    @abstractmethod
    def label(self) -> str:
        """Human-readable display name shown in the UI (e.g. 'Loved Jeans')."""
        ...

    @abstractmethod
    def upload_images(self, paths: str, sku: str, title: str, display) -> list | None:
        """Upload images. Returns list of hosted URLs, or None on failure."""
        ...

    @abstractmethod
    def upload_item(self, item: dict, display) -> str:
        """Upload item data. Returns an UploadResult."""
        ...
