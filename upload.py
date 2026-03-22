from concurrent.futures import ThreadPoolExecutor
import threading

import tools

SKU_LENGTH = 9


class EbayUpload:
    def __init__(self, accounts, ui, translator, upload_display, upload_changer, item_type, ebay_dest, website_dests):
        self.accounts = accounts
        self.item_type = item_type
        self.upload_mode = upload_changer
        self.ui = ui
        self.translator = translator
        self.UploadDisplay = upload_display
        self.ebay_dest = ebay_dest
        self.website_dests = website_dests
        self.stop_upload = False
        self.upload_begin = ""

    def update_connections(self):
        self.ebay_dest.update_connections()

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
                enabled_website_dests = []
            else:
                upload_countries = self.item_type.upload_data["upload_to"]
                enabled_website_dests = [
                    dest for dest in self.website_dests
                    if self.upload_mode.upload_state[self.upload_mode.OPTIONS.index(dest.name)]
                    and dest.name in upload_countries
                ]

            fast_images = self.upload_mode.upload_state[8]
            ebay_images = any(self.upload_mode.upload_state[:6])

            if ebay_images:
                item_pic_object = self.ebay_dest.upload_images(item["Path"], item["SKU"], self.display)
                print(item_pic_object)
                if not item_pic_object:
                    self.display.set_item_status(self.listing_number - 1, "Failure")
                    continue

            if enabled_website_dests:
                if fast_images:
                    item_pic_object = enabled_website_dests[0].upload_images(item["Path"], item["SKU"], item["Title"], self.display)
                    if not item_pic_object:
                        self.display.set_item_status(self.listing_number - 1, "Failure")
                        continue
                else:
                    for dest in enabled_website_dests:
                        dest.upload_images(item["Path"], item["SKU"], item["Title"], self.display)

            feedback = []
            with ThreadPoolExecutor() as executor:
                if ebay_images:
                    for site_num, details in enumerate(item_batch):
                        if self.upload_mode.OPTIONS[site_num] in upload_countries and details:
                            feedback.append(executor.submit(
                                self.ebay_dest.send_item, site_num, details, item_pic_object, self.listing_number, self.display
                            ))
                for dest in enabled_website_dests:
                    feedback.append(executor.submit(dest.upload_item, item, self.display))

            final_feedback = [fd.result() for fd in feedback]
            print(list(final_feedback))
            print("\n\n")
            final_feedback.sort(key=lambda x: x[:1])
            final_feedback = [ff[1:] for ff in final_feedback]

            worst_error = "Success"
            for reply in final_feedback:
                if "Failure" in reply:
                    worst_error = "Failure"
                    self.display.push_error(reply, item["SKU"])
                elif "Warning" in reply and worst_error != "Failure":
                    worst_error = "Warning"
                    self.display.push_error(reply, item["SKU"])
                elif worst_error != "Warning" and worst_error != "Failure":
                    worst_error = "Success"

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

            if not start_point:
                tools.display_error("The start SKU was not found")
                return None

            if extra_info and not end_point:
                tools.display_error("The end SKU was not found")
                return None

            if end_point:
                self.upload_items(self.ui.item_specifics[start_point : end_point + 1])
            else:
                self.upload_items(self.ui.item_specifics[start_point:])
