from abc import ABC, abstractmethod


class Destination(ABC):
    """Interface for upload destinations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used as the toggle key (e.g. 'SQL', 'UK')."""
        ...

    @property
    @abstractmethod
    def label(self) -> str:
        """Human-readable display name shown in the UI (e.g. 'Loved Jeans', 'UK')."""
        ...

    @abstractmethod
    def upload_images(self, paths: str, sku: str, title: str, display) -> list | None:
        """Upload images. Returns list of hosted URLs, or None on failure."""
        ...

    @abstractmethod
    def upload_item(self, item_batch, images: list | None, listing_number: int):
        """Upload item data. Returns an UploadResult."""
        ...

    def has_data(self, item_batch: list) -> bool:
        """Whether this destination has data for the given item batch.
        Defaults to True; eBay site destinations override this."""
        return True

    @property
    def fail_on_image_error(self) -> bool:
        """Whether a None return from upload_images should abort the whole item.
        True for eBay (images are required in the listing), False for website
        destinations (image failure is reported but the item upload continues)."""
        return True

    def clear_image_cache(self, sku: str):
        """Clear cached image upload result for this SKU. No-op by default."""
        pass

    def update_connection(self):
        """Refresh the API connection (e.g. after an account switch). No-op by default."""
        pass
