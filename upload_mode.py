import tkinter as tk


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

    def change_mode(self):
        self.win = tk.Tk()
        self.win.title("Change Upload Mode")
        self.win.geometry("250x300")

        row = 0
        self._ebay_vars = []
        for i, country in enumerate(self.EBAY_COUNTRIES):
            tk.Label(self.win, text=country).grid(row=row, column=0)
            var = tk.IntVar(self.win, value=self.upload_state[i])
            tk.Checkbutton(self.win, variable=var, command=self._on_change).grid(row=row, column=1)
            self._ebay_vars.append(var)
            row += 1

        self._website_vars = {}
        for dest in self._website_dests:
            tk.Label(self.win, text=dest.label).grid(row=row, column=0)
            var = tk.IntVar(self.win, value=int(self._website_state.get(dest.name, False)))
            tk.Checkbutton(self.win, variable=var, command=self._on_change).grid(row=row, column=1)
            self._website_vars[dest.name] = var
            row += 1

        tk.Label(self.win, text="Fast images").grid(row=row, column=0)
        self._fast_images_var = tk.IntVar(self.win, value=int(self.fast_images))
        tk.Checkbutton(self.win, variable=self._fast_images_var, command=self._on_change).grid(row=row, column=1)
        row += 1

        tk.Label(self.win, text="Download images with items").grid(row=row, column=0)
        self._download_images_var = tk.IntVar(self.win, value=int(self.download_images))
        tk.Checkbutton(self.win, variable=self._download_images_var, command=self._on_change).grid(row=row, column=1)

    def _on_change(self):
        for i, var in enumerate(self._ebay_vars):
            self.upload_state[i] = var.get()
        for name, var in self._website_vars.items():
            self._website_state[name] = bool(var.get())
        self.fast_images = bool(self._fast_images_var.get())
        self.download_images = bool(self._download_images_var.get())
