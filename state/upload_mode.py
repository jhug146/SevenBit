class UploadMode:
    EBAY_COUNTRIES = ("US", "UK", "AUS", "FRA", "GER", "ITA", "SPA")
    OPTIONS = ("US", "UK", "AUS", "FR", "DE", "IT", "ES")

    def __init__(self, item_type):
        self.item_type = item_type
        self._website_dests = []
        self.fix_mode()

    def fix_mode(self):
        upload_to = self.item_type.upload_data["upload_to"]
        self.upload_state = [1 if opt in upload_to else 0 for opt in self.OPTIONS]
        self.fast_images = "IMG" in upload_to
        self.download_images = "DIMG" in upload_to
        self._website_state = {dest.name: (dest.name in upload_to) for dest in self._website_dests}

    def register(self, all_dests):
        """Call after destinations are created. Builds per-destination toggle state.
        Accepts the full destination list; separates eBay sites (already in upload_state)
        from website destinations (stored in _website_state dict)."""
        upload_to = self.item_type.upload_data["upload_to"]
        self._website_dests = [d for d in all_dests if d.name not in self.OPTIONS]
        self._website_state = {dest.name: (dest.name in upload_to) for dest in self._website_dests}

    def is_destination_enabled(self, name: str) -> bool:
        if name in self.OPTIONS:
            return bool(self.upload_state[self.OPTIONS.index(name)])
        return self._website_state.get(name, False)
