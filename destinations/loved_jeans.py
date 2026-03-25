import json
import pathlib
import requests

import tools
from image_store import ImageStore
from destinations.base import Destination
from upload_result import UploadResult, UploadStatus


class WebsiteDestination(Destination):
    """Handles image and item uploads to a custom website (e.g. lovedjeans.co.uk)."""

    def __init__(self, item_type):
        self.item_type = item_type
        self.client = requests.session()
        self._image_store = ImageStore()

    @property
    def name(self) -> str:
        return "SQL"

    @property
    def label(self) -> str:
        return "Loved Jeans"

    @property
    def fail_on_image_error(self) -> bool:
        # A website image failure is reported in the display but does not abort the
        # item — the item upload continues. eBay fast_images mode still works
        # correctly because the EbayImageStore calls this method directly and will
        # propagate the None to the EbaySiteDestination, which does fail on None.
        return False

    def clear_image_cache(self, sku: str):
        self._image_store.clear(sku)

    def upload_images(self, paths: str, sku: str, title: str, display, no_urls: bool = False) -> list | None:
        # no_urls=True is a special caller-side flag that changes the return type.
        # Bypass the cache so a no_urls call never pollutes the cached list result.
        if no_urls:
            return self._do_upload_images(paths, sku, title, display, no_urls=True)
        return self._image_store.get(sku, self._do_upload_images, paths, sku, title, display)

    def _do_upload_images(self, paths: str, sku: str, title: str, display, no_urls: bool = False) -> list | None:
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
                response = self.client.post(URL, data=data)
            else:
                images = {}
                for i, name in enumerate(path_list):
                    with open(pathlib.Path(name), "rb") as f:
                        images[f"file{i}"] = f.read()
                response = self.client.post(URL, data=data, files=images)

            if no_urls:
                return response.text[:7]

            urls = json.loads(response.text[27:])   # cuts off the "Success - Images Uploaded" bit
            if type(urls) is list:
                return urls
            else:
                raise Exception(f"Image upload error - Unable to parse {response.text}")

        except Exception as e:
            display.push_error(e, sku)
            return None

    def upload_item(self, item_batch: list, images, listing_number: int, display) -> UploadResult:
        item = item_batch[1] if (len(item_batch) > 1) else item_batch[0]
        upload_data = self.item_type.upload_data
        website_data = upload_data["website"]["item"]
        to_upload = {}
        order = zip(upload_data["upload_ordering"], upload_data["detail_ordering"])
        for key, value in order:
            to_upload[value] = item[key]

        to_upload["paths"] = ";" * (item["Path"].count(";") - 1)
        try:
            response = self.client.post(
                upload_data["website"]["url"] + website_data["url"],
                data={
                    "item": json.dumps(to_upload),
                    "username": website_data["username"],
                    "password": website_data["password"]
                }
            )
            status = UploadStatus.SUCCESS if "Success" in response.text else UploadStatus.FAILURE
            return UploadResult(status, sort_key=7, message="Website returned: " + response.text)
        except Exception as e:
            return UploadResult(UploadStatus.FAILURE, sort_key=7, message=str(e))
