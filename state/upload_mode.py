class UploadMode:
    def __init__(self, upload_config, ebay_labels, ebay_options):
        self.upload_config = upload_config
        self.ebay_labels = ebay_labels
        self.ebay_options = ebay_options
        self._website_dests = []
        self.fix_mode()

    def fix_mode(self):
        default_sites = self.upload_config.default_sites
        self.upload_state = [1 if opt in default_sites else 0 for opt in self.ebay_options]
        self.fast_images = "IMG" in default_sites
        self.download_images = "DIMG" in default_sites
        self._website_state = {dest.name: (dest.name in default_sites) for dest in self._website_dests}

    def register(self, all_dests):
        """Call after destinations are created. Builds per-destination toggle state.
        Accepts the full destination list; separates eBay sites (already in upload_state)
        from website destinations (stored in _website_state dict)."""
        default_sites = self.upload_config.default_sites
        self._website_dests = [d for d in all_dests if d.name not in self.ebay_options]
        self._website_state = {dest.name: (dest.name in default_sites) for dest in self._website_dests}

    def apply_allowed_destinations(self, allowed):
        if allowed is None:
            return
        for i, opt in enumerate(self.ebay_options):
            if opt not in allowed:
                self.upload_state[i] = 0
        for name in self._website_state:
            if name not in allowed:
                self._website_state[name] = False

    def is_destination_enabled(self, name: str) -> bool:
        if name in self.ebay_options:
            return bool(self.upload_state[self.ebay_options.index(name)])
        return self._website_state.get(name, False)

    def any_website_enabled(self) -> bool:
        return any(self._website_state.values())
