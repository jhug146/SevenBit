from __future__ import annotations

import json
import pathlib
import requests

from upload.destinations.image_store import ImageStore
from upload.destinations.base import Destination
from upload.models.upload_result import UploadResult, UploadStatus


class WebsiteDestination(Destination):
    """Handles image and item uploads to a custom website (e.g. lovedjeans.co.uk)."""

    def __init__(self, upload_config):
        self.upload_config = upload_config
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

    def upload_images(self, paths: str, sku: str, title: str, display) -> list | None:
        return self._image_store.get(sku, self._do_upload_images, paths, sku, title, display)

    def _do_upload_images(self, paths: str, sku: str, title: str, display) -> list | None:
        website_data = self.upload_config.website_images
        url = self.upload_config.website_url + website_data["url"]

        path_list = paths.split(";")
        while path_list[-1] == "":
            path_list.pop()

        using_urls = "http" in path_list[0]
        data = {
            "username": website_data["username"],
            "password": website_data["password"],
            "sku": sku,
            "title": title,
            "urls": json.dumps(path_list) if using_urls else "file"
        }

        try:
            if using_urls:
                response = self.client.post(url, data=data)
            else:
                images = {}
                for i, name in enumerate(path_list):
                    with open(pathlib.Path(name), "rb") as f:
                        images[f"file{i}"] = f.read()
                response = self.client.post(url, data=data, files=images)

            result = json.loads(response.text[len("Success - Images Uploaded"):])

            if isinstance(result, list):
                return result
            raise Exception(f"Image upload error - Unable to parse {response.text}")

        except Exception as e:
            display.push_error(e, sku)
            return None

    def upload_item(self, item_batch, images, listing_number: int) -> UploadResult:
        item = item_batch.default
        website_data = self.upload_config.website_item
        to_upload = {}
        for key, value in self.upload_config.field_mapping.items():
            to_upload[value] = item[key]

        to_upload["paths"] = ";" * (item_batch.images.count(";") - 1)
        try:
            response = self.client.post(
                self.upload_config.website_url + website_data["url"],
                data={
                    "item": json.dumps(to_upload),
                    "username": website_data["username"],
                    "password": website_data["password"]
                }
            )
            status = UploadStatus.SUCCESS if "Success" in response.text else UploadStatus.FAILURE
            return UploadResult(status, message="Website returned: " + response.text)
        except Exception as e:
            return UploadResult(UploadStatus.FAILURE, message=str(e))
