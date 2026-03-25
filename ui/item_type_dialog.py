import tkinter as tk

from ui.utils import display_error


class ItemTypeDialog:
    def __init__(self, item_type, on_success):
        self.item_type = item_type
        self.on_success = on_success
        self.win = None

    def show(self):
        try:
            self.win.winfo_exists()
            return None
        except (tk.TclError, AttributeError):
            pass

        self.item_type.get_info()
        self.win = tk.Tk()
        self.win.title("Items Configuration")

        tk.Label(self.win, text="Enter product name specified in .csv file: ").grid(row=0, column=0)
        self.choose_var = tk.StringVar(self.win)
        self.choose_type = tk.Entry(self.win, textvariable=self.choose_var)
        self.choose_type.grid(row=1, column=0)
        self.choose_type.bind("<Return>", self._confirm)
        self.choose_type.focus()

    def _confirm(self, _):
        name = self.choose_var.get()
        self.win.destroy()
        if not name:
            return None
        try:
            self.item_type.get_info(name)
            self.on_success()
        except:
            display_error(f"The specified item name: {name} could not be found")
