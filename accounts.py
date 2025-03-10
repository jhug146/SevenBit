"""
Accounts class
"""
import tkinter as tk
import json

import tools

class Accounts:

    def __init__(self, ui, item_type):
        self.ui = ui
        self.item_type = item_type
        self.account_data = tools.load_json_file("user/accounts.json")
        self.accounts_choice = self.account_data[self.account_data["default"]]
        self.update_title()

    def set_upload_attr(self, upload):
        self.upload = upload

    def update_title(self):
        self.ui.window.title(f"SevenBit - {self.accounts_choice['name']} - {self.item_type.upload_data['name']}")

    def choose(self):
        """
        Chooses the account selected in the choose_account method
        :return: None
        """
        try:
            self.accounts_choice = self.account_data[self.account_entry.get()]
            self.dwin.destroy()
            self.update_title()
            self.upload.update_connections()
        except (ValueError, KeyError):
            tools.display_error(f"The account: {self.account_entry.get()} was not found")

    def choose_account(self):
        """
        Gets the name of the account the user would like to use
        :return: None
        """
        with open("user/accounts.json", encoding="utf-8") as file:
            self.account_data = json.load(file)

        self.to_choose = tk.StringVar(value="")
        self.dwin = tk.Toplevel()
        self.dwin.title("Choose account")
        self.dwin.geometry("120x45")
        self.dwin.iconphoto(False, tk.PhotoImage(file="images/icon.png"))

        tk.Label(self.dwin, text="Enter account name:").grid(row=0, column=0)
        self.account_entry = tk.Entry(self.dwin, textvariable=self.to_choose)
        self.account_entry.focus()
        self.account_entry.grid(row=1, column=0)
        #tk.Button(self.dwin, text="Confirm", font=self.ui.big_font, command=self.choose).grid(row=2, column=0)
        self.account_entry.bind("<Return>", lambda x: self.choose())
