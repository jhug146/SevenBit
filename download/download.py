from ebaysdk.shopping import Connection as ShoppingConnection

from urllib.request import urlopen
from PIL import Image
import os
import csv
import json
import requests


ITEM_NUMBER_LENGTH = 12


def none_to_str(word):
    return "" if word is None else word


def split_list(to_split, length):
    for i in range(0, len(to_split), length):
        yield to_split[i:i + length]


def write_csv(file, data):
    with open(file, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=",")
        for row in data:
            csvwriter.writerow(row)


def check_int(num):
    try:
        num = str(int(num))
        return num if len(num) == ITEM_NUMBER_LENGTH else None
    except (ValueError, TypeError):
        return None


def split_numbers(nums):
    nums = nums.replace(" ", "")
    if "," in nums:
        return nums.split(",")
    elif ";" in nums:
        return nums.split(";")
    elif "\n" in nums:
        return nums.split("\n")
    else:
        return [nums[i:i+ITEM_NUMBER_LENGTH] for i in range(0, len(nums), ITEM_NUMBER_LENGTH)]


class GetItems(object):
    UPLOAD_BATCH_SIZE = 20
    def __init__(self, accounts, download_config, upload_changer, on_error):
        self.accounts = accounts
        self.download_config = download_config
        self.upload_mode = upload_changer
        self.on_error = on_error

        self.connection = ShoppingConnection(
            config_file = None,
            appid = accounts.appid,
            debug = False
        )
        self.file_count = 0

    def get_token(self):
        response = requests.post(
            "https://api.ebay.com/oauth/api_scope",
            data={"grant_type": "client_credentials"},
            auth=(self.accounts.appid, self.accounts.certid),
        )
        return response.json()["access_token"]

    def get_column_num(self, name):
        return self.download_config.headers.index(name)

    def get_items(self, numbers):
        request = {
            "ItemID": numbers,
            "IncludeSelector":"Details,Description,ItemSpecifics",
        }
        response = self.connection.execute("GetMultipleItems", request, oauth=self.get_token().access_token).dict()
        print(response)
        if "Item" not in response:
            error = "One or more of the entered item ids were invalid" if response["Errors"]["ShortMessage"] == "Invalid item ID." else json.dumps(response["Errors"])
            self.on_error(error)
            return None

        item_list = response["Item"] if type(response["Item"]) is list else [response["Item"]]
        download_images = self.upload_mode.download_images

        set_values = self.download_config.set_values
        non_is_values = self.download_config.non_is_values
        is_values = self.download_config.is_values

        images_column = self.get_column_num("Path")
        price_column = self.get_column_num("Price")
        description_column = self.get_column_num("eBay Condition Description")

        gender = self.get_column_num("IS_Department")
        waist = self.get_column_num("Waist")
        length =  self.get_column_num("Tag L")

        items = []
        for item in item_list:
            row = [None] * len(self.download_config.headers)
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

            for new,original,start,end in self.download_config.substrings:
                try:
                    row[new] = row[original][start:end]
                    if "(" in row[new]:
                        row[new] = list(row[new])[0]
                except TypeError:
                    row[new] = ""

            row = [none_to_str(detail) for detail in row]
            items.append(row)

        return items

    def search_from_input(self, raw_input):
        nums = split_numbers(raw_input)
        numbers = [checked for num in nums if (checked := check_int(num))]
        if not numbers:
            return False
        numbers = [number.replace(" ", "") for number in numbers]
        self.search(numbers)
        return True

    def make_folder(self):
        i = 1
        self.folder = self.download_config.save_folder + "/image_folder-1"
        while os.path.exists(self.folder):
            self.folder = self.download_config.save_folder + f"/image_folder-{i}"
            i += 1
        try:
            os.mkdir(self.folder)
        except FileNotFoundError:
            self.on_error(f"Save location not found {self.folder} please check your accounts.csv file")
            return None
        return self.folder

    def search(self, numbers):
        if self.upload_mode.download_images:
            if not self.make_folder():
                return None

        data = [self.download_config.headers]
        for i,group in enumerate(split_list(numbers, self.UPLOAD_BATCH_SIZE)):
            items = self.get_items(group)
            if items:
                data.extend(items)

        save_file = self.download_config.save_folder + "/ebay-import.csv"
        try:
            write_csv(save_file, data)
            os.system(f"start excel.exe {save_file}")
        except PermissionError:
            self.on_error("Please close the ebay-import.csv file before attempting to download into it")

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
