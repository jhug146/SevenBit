import json
import pathlib
import requests

import tools
from destinations.base import Destination
from upload_result import UploadResult, UploadStatus


class WebsiteDestination(Destination):
    """Handles image and item uploads to a custom website (e.g. lovedjeans.co.uk)."""

    def __init__(self, item_type):
        self.item_type = item_type
        self.client = requests.session()

    @property
    def name(self) -> str:
        return "SQL"

    @property
    def label(self) -> str:
        return "Loved Jeans"

    def upload_images(self, paths: str, sku: str, title: str, display, no_urls: bool = False) -> list | None:
        website_data = self.item_type.upload_data["website"]["images"]
        URL = self.item_type.upload_data["website"]["url"] + website_data["url"]

        path_list = paths.split(";")
        if path_list[-1] == "":
            path_list.pop()

        try:
            if "http" in path_list[0]:
                urls = json.dumps(path_list)
            else:
                urls = "file"

            data = {
                "username": website_data["username"],
                "password": website_data["password"],
                "sku": sku,
                "title": title,
                "urls": urls
            }
            if "http" in path_list[0]:
                response = self.client.post(
                    URL,
                    data = data
                )
            else:
                images = {}
                for i, name in enumerate(path_list):
                    images[f"file{i}"] = open(pathlib.Path(name), "rb").read()
                response = self.client.post(
                    URL,
                    data = data,
                    files = images
                )
            if no_urls:
                return response.text[:7]

            urls = json.loads(response.text[27:])   #Cuts off the "Success - Images Uploaded" bit
            if type(urls) is list:
                return urls
            else:
                raise Exception(f"Image upload error - Unable to parse {response.text}")

        except Exception as e:
            display.push_error(e, sku)
            return None

    def upload_item(self, item: dict, display) -> str:
        upload_data = self.item_type.upload_data
        website_data = upload_data["website"]["item"]
        to_upload = {}
        order = zip(upload_data["upload_ordering"], upload_data["detail_ordering"])
        # Loops through the upload_ordering and detail_ordering arrays to map item to a format that the server accepts
        for key, value in order:
            to_upload[value] = item[key]
            # If specified in the json file, set certain columns to 0 instead of ""
            if (key in upload_data["blank_to_zero"]) and (tools.is_blank(value)):
                to_upload[value] = 0

        # No need to store all of image paths, just number of semicolons
        to_upload["paths"] = ";" * (item["Path"].count(";") - 1)
        try:
            response = self.client.post(
                upload_data["website"]["url"] + website_data["url"],
                data = {
                    "item": json.dumps(to_upload),
                    "username": website_data["username"],
                    "password": website_data["password"]
                }
            )
            status = UploadStatus.SUCCESS if "Success" in response.text else UploadStatus.FAILURE
            return UploadResult(status, sort_key=7, message="Website returned: " + response.text)
        except Exception as e:
            return UploadResult(UploadStatus.FAILURE, sort_key=7, message=str(e))
