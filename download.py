from ebaysdk.shopping import Connection as ShoppingConnection

import tkinter as tk
from urllib.request import urlopen
from PIL import Image
import os
import tools
import json
import requests


class GetItems(object):
    ITEM_NUMBER_LENGTH = 12
    UPLOAD_BATCH_SIZE = 20
    def __init__(self, accounts_choice, ui, item_type, upload_changer):
        self.ui = ui
        self.item_type = item_type
        self.upload_mode = upload_changer
        self.accounts_choice = accounts_choice
        acc = accounts_choice["credentials"]

        self.connection = ShoppingConnection(
            config_file = None,
            appid = acc["appid"],
            debug = False
        )
        self.file_count = 0

    def get_token(self):
        acc = self.accounts_choice["credentials"]
        response = requests.post(
            "https://api.ebay.com/oauth/api_scope",
            data={"grant_type": "client_credentials"},
            auth=(acc["appid"], acc["certid"]),
        )
        return response.json()["access_token"]

    def close_window(self):
        if hasattr(self, "entry_win"):
            self.entry_win.destroy()
            delattr(self, "entry_win")

    def get_numbers(self):
        if hasattr(self, "entry_win"):
            return None

        self.entry_win = tk.Toplevel(self.ui.window)
        self.entry_win.protocol("WM_DELETE_WINDOW", self.close_window)
        self.entry_win.title("Download")
        self.entry_win.iconphoto(False, tk.PhotoImage(file="images/icon.png"))
        self.entry_var = tk.StringVar(self.entry_win)

        tk.Label(self.entry_win, text="Enter list of item numbers seperated by commas").grid(row=0, column=0)
        self.entry = tk.Entry(self.entry_win, textvariable=self.entry_var)
        self.entry.focus()
        self.entry.grid(row=1, column=0)
        self.entry.bind("<Return>", lambda x: self.check_nums())

    def get_column_num(self, name):
        return self.download_data["headers"].index(name)

    def get_items(self, numbers):
        request = {
            "ItemID": numbers,
            "IncludeSelector":"Details,Description,ItemSpecifics",
        }
        response = self.connection.execute("GetMultipleItems", request, oauth=self.get_token().access_token).dict()
        print(response)
        if "Item" not in response:
            error = "One or more of the entered item ids were invalid" if response["Errors"]["ShortMessage"] == "Invalid item ID." else json.dumps(response["Errors"])
            tools.display_error(error)
            return None

        item_list = response["Item"] if type(response["Item"]) is list else [response["Item"]]
        download_images = self.upload_mode.upload_state[9]

        set_values = self.download_data["set_values"]
        non_is_values = self.download_data["non_is_values"]
        is_values = self.download_data["is_values"]

        images_column = self.get_column_num("Path")
        price_column = self.get_column_num("Fixed Price eBay")
        description_column = self.get_column_num("eBay Condition Description")

        category_column = self.get_column_num("eBay Store Category1Name")
        gender = self.get_column_num("IS_Department")
        waist = self.get_column_num("Waist")
        length =  self.get_column_num("Tag L")

        items = []
        for item in item_list:
            row = [None] * len(self.download_data["headers"])
            row[images_column] = self.get_images(item["PictureURL"] + [item["GalleryURL"]]) if download_images else ""

            for col,value in set_values.items():
                row[int(col)] = value

            for col,value in non_is_values.items():
                if col == str(price_column):
                    row[int(col)] = item[value]["value"]
                elif col == str(description_column):
                    row[int(col)] = ""
                else:
                    row[int(col)] = item[value]

            for namevalue in item["ItemSpecifics"]["NameValueList"]:
                if type(namevalue) is not str:
                    if namevalue["Name"] in is_values:
                        row[is_values[namevalue["Name"]]] = namevalue["Value"]

            for new,original,start,end in self.download_data["substrings"]:
                try:
                    row[new] = row[original][start:end]
                    if "(" in row[new]:
                        row[new] = list(row[new])[0]
                except TypeError:
                    row[new] = ""
            row[category_column] = f'{gender}s::Waist {waist}"::Leg {length}"'

            row = [tools.none_to_str(detail) for detail in row]
            items.append(row)

        return items

    def check_nums(self):
        self.close_window()
        nums = self.entry_var.get()
        nums = tools.split_numbers(nums)

        numbers = []
        for num in nums:
            num = tools.check_int(num)
            if num:
                numbers.append(num)

        if not numbers:
            self.close_window()
            tools.display_error("Invalid numbers entered")
            return None

        numbers = [number.replace(" ", "") for number in numbers]
        self.search(numbers)

    def make_folder(self):
        i = 1
        self.folder = self.download_data["save_folder"] + "/image_folder-1"
        while os.path.exists(self.folder):
            self.folder = self.download_data["save_folder"] + f"/image_folder-{i}"
            i += 1
        try:
            os.mkdir(self.folder)
        except FileNotFoundError:
            tools.display_error(f"Save location not found {self.folder} please check your accounts.csv file")
            return None
        return self.folder

    def search(self, numbers):
        self.download_data = self.item_type.download_data

        if self.upload_mode.upload_state[9]:
            if not self.make_folder():
                return None

        data = [self.download_data["headers"]]
        for i,group in enumerate(tools.split_list(numbers, self.UPLOAD_BATCH_SIZE)):
            items = self.get_items(group)
            if items:
                data.extend(items)

        save_file = self.download_data["save_folder"] + "/ebay-import.csv"
        try:
            tools.write_csv(save_file, data)
            os.system(f"start excel.exe {save_file}")
        except PermissionError:
            tools.display_error("Please close the ebay-import.csv file before attempting to download into it")

    def get_images(self, urls):
        """
        Saves the images off of the entered urls and returns their combined paths
        :param urls: list
        :return: string
        """
        paths = []
        for i,url in enumerate(urls[:-1]):
            try:
                img = Image.open(urlopen(url.replace("$_1", "$_10")))
            except:
                raise Exception("Error with https://i.ebayimg.com")
            paths.append(f"{self.folder}/E{self.file_count}.jpg")
            img.save(paths[i])
            self.file_count += 1
        return ";".join(paths) + ";"
