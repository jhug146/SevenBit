import tkinter as tk

from ui.utils import display_error


class DownloadDialog:
    def __init__(self, parent_window, get_items):
        self.parent_window = parent_window
        self.get_items = get_items

    def show(self):
        if hasattr(self, "win"):
            return None

        self.win = tk.Toplevel(self.parent_window)
        self.win.protocol("WM_DELETE_WINDOW", self._close)
        self.win.title("Download")
        self.win.iconphoto(False, tk.PhotoImage(file="images/icon.png"))
        self.entry_var = tk.StringVar(self.win)

        tk.Label(self.win, text="Enter list of item numbers seperated by commas").grid(row=0, column=0)
        self.entry = tk.Entry(self.win, textvariable=self.entry_var)
        self.entry.focus()
        self.entry.grid(row=1, column=0)
        self.entry.bind("<Return>", lambda x: self._confirm())

    def _close(self):
        if hasattr(self, "win"):
            self.win.destroy()
            delattr(self, "win")

    def _confirm(self):
        raw = self.entry_var.get()
        self._close()
        if not self.get_items.search_from_input(raw):
            display_error("Invalid numbers entered")
