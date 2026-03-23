from concurrent.futures import ThreadPoolExecutor
import threading

import tools
from upload_result import UploadStatus

SKU_LENGTH = 9


class EbayUpload:
    def __init__(self, accounts, ui, translator, upload_display, upload_changer, item_type, destinations):
        self.accounts = accounts
        self.item_type = item_type
        self.upload_mode = upload_changer
        self.ui = ui
        self.translator = translator
        self.UploadDisplay = upload_display
        self.all_dests = destinations
        self.stop_upload = False
        self.upload_begin = ""

    def update_connections(self):
        for dest in self.all_dests:
            dest.update_connection()

    def upload_items(self, en_listings):
        self.items_thread = threading.Thread(target=self.upload_items_thread, args=(en_listings,))
        self.items_thread.start()

    def upload_items_thread(self, en_listings):
        print("Translating...")
        listings = self.translator.translate(en_listings)

        print("Uploading...")
        self.display = self.UploadDisplay(listings, self.ui, self)

        self.length = len(listings)
        self.listing_number = 0

        account_data = self.accounts.accounts_choice
        for item_batch in listings:
            self.listing_number += 1
            item = item_batch[1] if (len(item_batch) > 1) else item_batch[0]
            if self.stop_upload:
                self.stop_upload = False
                tools.display_error(f"Upload stopped on this SKU: {item['SKU']}")
                break

            if account_data["default_uploads"]:
                upload_countries = account_data["default_uploads"]
            else:
                upload_countries = self.item_type.upload_data["upload_to"]

            enabled_dests = [
                d for d in self.all_dests
                if d.name in upload_countries
                and self.upload_mode.is_destination_enabled(d.name)
                and d.has_data(item_batch)
            ]

            # Reset image caches so each item gets a fresh upload
            for dest in self.all_dests:
                dest.clear_image_cache(item["SKU"])

            # Phase 1: upload images for each enabled destination sequentially.
            # EbaySiteDestinations all share one EbayImageStore, so only the first
            # one triggers a real upload — the rest return the cached result instantly.
            # WebsiteDestination also caches, so it uploads at most once even if
            # called by both the EbayImageStore (fast_images mode) and directly here.
            image_results = {}
            upload_failed = False
            for dest in enabled_dests:
                images = dest.upload_images(item["Path"], item["SKU"], item["Title"], self.display)
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
                        self.display.push_error(result.message, item["SKU"])
                elif result.status == UploadStatus.WARNING and worst_error != UploadStatus.FAILURE:
                    worst_error = UploadStatus.WARNING
                    if result.message:
                        self.display.push_error(result.message, item["SKU"])

            self.display.set_item_status(self.listing_number - 1, worst_error)
            self.ui.window.update()

        print("Upload complete")

    def set_upload(self, value):
        self.stop_upload = value

    def confirm_upload(self):
        errors = False
        line_nums = []
        try:
            if type(self.ui.item_specifics) is str:
                return None
        except AttributeError:
            return None

        requirements = self.item_type.upload_data["upload_requirements"]
        for i, item in enumerate(self.ui.item_specifics):
            is_title_short = (len(item["Title"]) > requirements["max_title_length"])
            is_price_over = (float(item["Fixed Price eBay"]) > requirements["max_price"])
            is_price_under = (float(item["Fixed Price eBay"]) < requirements["min_price"])

            if any((is_title_short, is_price_under, is_price_over)):
                line_nums.append(i)
                errors = True

        if errors:
            self.ui.outline_item(line_nums, True)
        else:
            self.ui.get_options(self, self.upload_begin)

    def start_upload(self, upload_type, info, extra_info=None):
        # Normal upload
        if upload_type == 0:
            self.upload_items(self.ui.item_specifics)

        # Specific SKUs upload
        elif upload_type == 1:
            if "," in info:
                skus = [x.upper() for x in info.split(",")]
            else:
                info = info.strip()
                skus = [x for x in tools.chunkstring(info, SKU_LENGTH)]
            items = [item for item in self.ui.item_specifics if (item["SKU"].upper() in skus)]
            if items:
                self.upload_items(items)
            else:
                tools.display_error("None of these SKUs were found")

        # Starting point upload
        elif upload_type == 2:
            start_point = None
            end_point = None
            for i, item in enumerate(self.ui.item_specifics):
                if item["SKU"].upper() in info.upper():
                    start_point = i
                if extra_info and item["SKU"].upper() in extra_info.upper():
                    end_point = i

            if start_point is None:
                tools.display_error("The start SKU was not found")
                return None

            if extra_info and not end_point:
                tools.display_error("The end SKU was not found")
                return None

            if end_point:
                self.upload_items(self.ui.item_specifics[start_point : end_point + 1])
            else:
                self.upload_items(self.ui.item_specifics[start_point:])
