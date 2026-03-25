import tkinter as tk
import json

from ui.utils import display_error


class AccountDialog:
    def __init__(self, accounts, on_success):
        self.accounts = accounts
        self.on_success = on_success

    def show(self):
        with open("user/accounts.json", encoding="utf-8") as file:
            self.accounts.account_data = json.load(file)

        self.entry_var = tk.StringVar(value="")
        self.win = tk.Toplevel()
        self.win.title("Choose account")
        self.win.geometry("120x45")
        self.win.iconphoto(False, tk.PhotoImage(file="images/icon.png"))

        tk.Label(self.win, text="Enter account name:").grid(row=0, column=0)
        self.entry = tk.Entry(self.win, textvariable=self.entry_var)
        self.entry.focus()
        self.entry.grid(row=1, column=0)
        self.entry.bind("<Return>", lambda x: self._confirm())

    def _confirm(self):
        name = self.entry.get()
        if self.accounts.switch_account(name):
            self.win.destroy()
            self.on_success()
        else:
            display_error(f"The account: {name} was not found")
