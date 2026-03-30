import tkinter as tk


class UploadModeDialog:
    def __init__(self, upload_mode, accounts):
        self.upload_mode = upload_mode
        self.accounts = accounts

    def show(self):
        self.win = tk.Tk()
        self.win.title("Change Upload Mode")
        self.win.geometry("250x300")

        allowed = self.accounts.allowed_destinations

        row = 0
        self._ebay_vars = []
        for i, country in enumerate(self.upload_mode.ebay_labels):
            opt = self.upload_mode.ebay_options[i]
            if allowed is not None and opt not in allowed:
                self._ebay_vars.append(None)
                continue
            tk.Label(self.win, text=country).grid(row=row, column=0)
            var = tk.IntVar(self.win, value=self.upload_mode.upload_state[i])
            tk.Checkbutton(self.win, variable=var, command=self._on_change).grid(row=row, column=1)
            self._ebay_vars.append(var)
            row += 1

        self._website_vars = {}
        for dest in self.upload_mode._website_dests:
            if allowed is not None and dest.name not in allowed:
                continue
            tk.Label(self.win, text=dest.label).grid(row=row, column=0)
            var = tk.IntVar(self.win, value=int(self.upload_mode._website_state.get(dest.name, False)))
            tk.Checkbutton(self.win, variable=var, command=self._on_change).grid(row=row, column=1)
            self._website_vars[dest.name] = var
            row += 1

        tk.Label(self.win, text="Fast images").grid(row=row, column=0)
        self._fast_images_var = tk.IntVar(self.win, value=int(self.upload_mode.fast_images))
        tk.Checkbutton(self.win, variable=self._fast_images_var, command=self._on_change).grid(row=row, column=1)
        row += 1

        tk.Label(self.win, text="Download images with items").grid(row=row, column=0)
        self._download_images_var = tk.IntVar(self.win, value=int(self.upload_mode.download_images))
        tk.Checkbutton(self.win, variable=self._download_images_var, command=self._on_change).grid(row=row, column=1)

    def _on_change(self):
        for i, var in enumerate(self._ebay_vars):
            if var is not None:
                self.upload_mode.upload_state[i] = var.get()
        for name, var in self._website_vars.items():
            self.upload_mode._website_state[name] = bool(var.get())
        self.upload_mode.fast_images = bool(self._fast_images_var.get())
        self.upload_mode.download_images = bool(self._download_images_var.get())
