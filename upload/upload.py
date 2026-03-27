from concurrent.futures import ThreadPoolExecutor
import threading
from dataclasses import dataclass
from typing import Callable

from upload.models.upload_result import UploadStatus


@dataclass
class UploadCallbacks:
    on_validation_error: Callable
    on_request_options: Callable
    on_tick: Callable
    on_error: Callable


def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))

SKU_LENGTH = 9


class Upload:
    def __init__(self, accounts, translator, make_display, upload_changer, upload_config, destinations, item_list,
                 upload_callbacks: UploadCallbacks):
        self.accounts = accounts
        self.upload_config = upload_config
        self.upload_mode = upload_changer
        self.item_list = item_list
        self.translator = translator
        self.make_display = make_display
        self.all_dests = destinations
        self.stop_upload = False
        self.upload_begin = ""
        self.on_validation_error = upload_callbacks.on_validation_error
        self.on_request_options = upload_callbacks.on_request_options
        self.on_tick = upload_callbacks.on_tick
        self.on_error = upload_callbacks.on_error

    def update_connections(self):
        for dest in self.all_dests:
            dest.update_connection()
        self.upload_mode.apply_allowed_destinations(self.accounts.allowed_destinations)

    def upload_items(self, en_listings):
        self.items_thread = threading.Thread(target=self.upload_items_thread, args=(en_listings,))
        self.items_thread.start()

    def upload_items_thread(self, en_listings):
        print("Translating...")
        listings = self.translator.translate(en_listings)

        print("Uploading...")
        self.display = self.make_display(listings, self)

        self.listing_number = 0

        for item_batch in listings:
            self.listing_number += 1
            item = item_batch[1] if (len(item_batch) > 1) else item_batch[0]
            if self.stop_upload:
                self.stop_upload = False
                self.on_error(f"Upload stopped on this SKU: {item.sku}")
                break

            upload_countries = self.upload_config.upload_to
            enabled_dests = [
                d for d in self.all_dests
                if d.name in upload_countries
                and self.upload_mode.is_destination_enabled(d.name)
                and d.has_data(item_batch)
            ]

            # Reset image caches so each item gets a fresh upload
            for dest in self.all_dests:
                dest.clear_image_cache(item.sku)

            # Phase 1: upload images for each enabled destination sequentially.
            # EbaySiteDestinations all share one EbayImageStore, so only the first
            # one triggers a real upload — the rest return the cached result instantly.
            # WebsiteDestination also caches, so it uploads at most once even if
            # called by both the EbayImageStore (fast_images mode) and directly here.
            image_results = {}
            upload_failed = False
            for dest in enabled_dests:
                images = dest.upload_images(item.images, item.sku, item.title, self.display)
                print(images)
                if images is None and (dest.fail_on_image_error or self.upload_mode.fast_images):
                    self.display.set_item_status(self.listing_number - 1, UploadStatus.FAILURE)
                    upload_failed = True
                    break
                image_results[dest] = images

            if upload_failed:
                continue

            # Phase 2: upload items in parallel, each destination receiving the
            # image URLs that its own upload_images call returned.
            feedback = []
            with ThreadPoolExecutor() as executor:
                for dest in enabled_dests:
                    feedback.append(executor.submit(
                        dest.upload_item, item_batch, image_results[dest], self.listing_number, self.display
                    ))

            final_feedback = sorted(
                [fd.result() for fd in feedback],
                key=lambda r: r.sort_key
            )
            print(final_feedback)
            print("\n\n")

            worst_error = UploadStatus.SUCCESS
            for result in final_feedback:
                if result.status == UploadStatus.FAILURE:
                    worst_error = UploadStatus.FAILURE
                    if result.message:
                        self.display.push_error(result.message, item.sku)
                elif result.status == UploadStatus.WARNING and worst_error != UploadStatus.FAILURE:
                    worst_error = UploadStatus.WARNING
                    if result.message:
                        self.display.push_error(result.message, item.sku)

            self.display.set_item_status(self.listing_number - 1, worst_error)
            self.on_tick()

        print("Upload complete")

    def set_upload(self, value):
        self.stop_upload = value

    def request_upload(self):
        if not isinstance(self.item_list.items, list):
            return

        error_line_nums = []
        for i, item in enumerate(self.item_list.items):
            is_title_long = len(item.title) > self.upload_config.max_title_length
            is_price_over = float(item.price) > self.upload_config.max_price
            is_price_under = float(item.price) < self.upload_config.min_price

            if any((is_title_long, is_price_under, is_price_over)):
                error_line_nums.append(i)

        if error_line_nums:
            self.on_validation_error(error_line_nums, True)
        else:
            self.on_request_options(self, self.upload_begin)

    def upload_all(self):
        self.upload_items(self.item_list.items)

    def upload_skus(self, raw: str):
        if "," in raw:
            skus = [x.strip().upper() for x in raw.split(",")]
        else:
            skus = [x for x in chunkstring(raw.strip(), SKU_LENGTH)]
        items = [item for item in self.item_list.items if item.sku.upper() in skus]
        if items:
            self.upload_items(items)
        else:
            self.on_error("None of these SKUs were found")

    def upload_from(self, start: str, end: str = ""):
        start_point = None
        end_point = None
        for i, item in enumerate(self.item_list.items):
            if item.sku.upper() in start.upper():
                start_point = i
            if end and item.sku.upper() in end.upper():
                end_point = i

        if start_point is None:
            self.on_error("The start SKU was not found")
            return

        if end and end_point is None:
            self.on_error("The end SKU was not found")
            return

        if end_point is not None:
            self.upload_items(self.item_list.items[start_point : end_point + 1])
        else:
            self.upload_items(self.item_list.items[start_point:])
