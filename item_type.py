"""
Handles different types of item to upload
Data from the html.csv file
"""
import tkinter as tk
import tools


class ItemType:
    def __init__(self):
        self.win = None
        self.get_info()

    def set_accounts_attr(self, accounts):
        self.accounts = accounts

    def get_info(self, name="default"):
        self.translation_data = tools.load_json_file("user/translation.json", name)
        self.upload_data = tools.load_json_file("user/upload.json", name)
        self.download_data = tools.load_json_file("user/download.json")

        if hasattr(self, "accounts"):
            self.accounts.update_title()

    def pass_upload(self, upload_mode):
        self.upload_mode = upload_mode

    def edit(self):
        try:
            self.win.winfo_exists()
            return None
        except (tk.TclError, AttributeError):
            pass

        self.get_info()
        self.win = tk.Tk()
        self.win.title("Items Configuration")

        tk.Label(self.win, text="Enter product name specified in .csv file: ").grid(row=0, column=0)
        self.choose_var = tk.StringVar(self.win)
        self.choose_type = tk.Entry(self.win, textvariable=self.choose_var)
        self.choose_type.grid(row=1, column=0)
        self.choose_type.bind("<Return>", self.choose_item_type)
        self.choose_type.focus()

    def choose_item_type(self, _):
        name = self.choose_var.get()
        self.win.destroy()
        if not name:
            return None
        try:
            self.get_info(name)
        except:
            tools.display_error(f"The specified item name: {name} could not be found")
