from ebaysdk.trading import Connection as TradingConnection

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pathlib
import json
import threading

import tools

SKU_LENGTH = 9

class EbayUpload:
    SITE_ABBRS = ("US", "UK", "Australia", "France", "Germany", "Italy", "Spain")
    SITE_IDS = ("0", "3", "15", "71", "77", "101", "186")
    SITE_NAMES = ("ebay.com", "ebay.co.uk", "ebay.com.au", "ebay.fr", "ebay.de", "ebay.it", "ebay.es")
    SITE_CURRS = ("USD", "GBP", "AUD", "EUR", "EUR", "EUR", "EUR")

    def __init__(self, accounts, ui, translator, upload_display, upload_changer, item_type):
        self.accounts = accounts
        self.item_type = item_type
        self.upload_mode = upload_changer
        self.ui = ui
        self.translator = translator
        self.UploadDisplay = upload_display
        self.stop_upload = False
        self.upload_begin = ""
        self.client = requests.session()
        self.update_connections()

    def update_connections(self):
        self.connections = []
        acc = self.accounts.accounts_choice["credentials"]

        for siteID in self.SITE_IDS:
            self.connections.append(TradingConnection(
                config_file = None,
                siteid = siteID,
                devid = acc["devid"],
                certid = acc["certid"],
                token = acc["token"],
                appid = acc["appid"],
                domain = "api.ebay.com",
                debug = False
            ))

    def upload_to_database(self, item):
        """
        Uploads to an sql database
        :param item: list
        :return: string
        """
        upload_data = self.item_type.upload_data
        website_data = upload_data["website"]["item"]
        to_upload = {}
        order = zip(upload_data["upload_ordering"], upload_data["detail_ordering"])
        # Loops through the upload_ordering and detail_ordering arrays to map item to a format that the server accepts
        for key,value in order: 
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
            self.display.push_error(response.text)
            if "Success" in response.text:
                return "9Success"
            else:
                return "9Failure"
        except Exception as e:
            self.display.push_error(e)
            return "9Failure"

    def upload_pic(self, path, pic_id):
        """
        Uploads the picture in the inputted path to the ebay image hosting site and return the url it's hosted at
        :param path: string
        :param pic_id: integer
        :return: string
        """
        image_data = open(path, "rb").read()  # When opening an image make sure to use read() so that the raw data is always used, this took 5+ hours to figure out!
        files = {"file": ("EbayImage", image_data)}
        while True:
            try:
                response = self.connections[0].execute("UploadSiteHostedPictures", self.item_type.upload_data["pictureData"], files=files)
                if "Ack" not in response.dict():
                    self.display.push_error(response.dict())
                    return str(pic_id) + "FailurePhotos"
                elif response.dict()["Ack"] == "Failure":
                    self.display.push_error(response.dict()["Errors"])
                    return str(pic_id) + "FailurePhotos"
            except Exception as error:
                self.display.push_error(error)
            else:
                break

        try:
            return str(pic_id) + response.dict()["SiteHostedPictureDetails"]["PictureSetMember"][0]["MemberURL"]
        except KeyError as key_error:
            self.display.push_error(key_error)

    def website_upload_pics(self, paths, sku, title, no_urls=False):
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
                for i,name in enumerate(path_list):
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
            self.display.push_error(e)
            return None

    def make_pic_object(self, paths):
        """
        Controls the upload of the images in the parameter paths and returns a list of their urls
        :param paths: string
        :return: list
        """
        path_list = paths.split(";")
        if path_list[-1] == "":
            path_list.pop()

        is_urls = True
        for path in path_list:
            if not "http" in path:  # If the photos are uploaded there is no need to re-upload
                is_urls = False
                break

        if is_urls:
            return path_list

        url_response = []
        with ThreadPoolExecutor(max_workers=12) as executor:
            urls = []
            for i,path in enumerate(path_list):
                # Each image is uploaded in its own thread to save time
                url_response.append(executor.submit(self.upload_pic, path, i))

            for ur in as_completed(url_response):
                result = ur.result()
                if result:
                    urls.append(result)

        # Image urls are sorted by their first character since the threads can end at different time causing the order to be wrong
        # Their first character is added in the upload_pic function based on which thread it's in
        for url in urls:
            if "FailurePhotos" in url:
                return None

        urls.sort(key=lambda x: x[:1])
        urls = [u.lstrip("0123456789") for u in urls]
        return urls

    def send_item(self, site_num, details, pic_object):
        if len(details) == 1:
            details = details[0]

        if not self.upload_mode.upload_state[site_num]:    # Use this for uploading to only non UK sites
            return f"{site_num}Success"

        upload_data = self.item_type.upload_data
        account_data = self.accounts.accounts_choice
        policies = account_data["policies"][upload_data["name"]]

        item_specific_list = []
        for detail in details:
            prefix, suffix = detail[:3], detail[3:]
            if prefix == "IS_" and upload_data["translate_headers"]:
                item_specific_list.append({
                    "Name": upload_data["is_names"][suffix][site_num],
                    "Value": details[detail]
                })
            elif (prefix == "MU_" or (prefix == "IS_" and not upload_data["translate_headers"])) and details[detail]:
                item_specific_list.append({
                    "Name": suffix,
                    "Value": details[detail]
                })

        html = details["eBay Description"].replace("&nbsp", "")

        if not policies["payment"][site_num]:
            return f"{site_num} Failure  -  You haven't specified a payment policy number for all the sites you're attempting to upload to on this account"

        payment_id = policies["payment"][site_num]
        shipping_id = policies["shipping"][site_num]
        returns_id = policies["returns"][site_num]

        store_category = account_data.get("default_store_category", details["eBay Store Category1ID"])
        request = {
            "Item": {
                "Title" : details["Title"],
                "SKU": details["SKU"],
                "Description": f"<![CDATA[{html}]]>",
                "ConditionDescription": details["eBay Condition Description"],
                "Country" : upload_data["user_info"]["country"],
                "Location": upload_data["user_info"]["country"],
                "Site" : self.SITE_ABBRS[site_num],
                "SiteId": self.SITE_IDS[site_num],
                "Currency": self.SITE_CURRS[site_num],
                "ConditionID": details["eBay Condition"],
                "PrimaryCategory": {
                    "CategoryID": str(details["eBay Category1ID"])
                },
                "ListingDuration": "GTC",
                "StartPrice": str(details["Fixed Price eBay"]),
                "SellerProfiles": {
                    "SellerPaymentProfile":  {
                        "PaymentProfileID":  payment_id
                    },
                    "SellerShippingProfile": {
                        "ShippingProfileID": shipping_id
                    },
                    "SellerReturnProfile":   {
                        "ReturnProfileID":   returns_id
                    }
                },
                "SellerContactDetails": {
                    "County": upload_data["user_info"]["county"]
                },
                "PostalCode": upload_data["user_info"]["postcode"],
                "Storefront": {
                    "StoreCategoryID": store_category
                },
                "ItemSpecifics": {
                    "NameValueList": item_specific_list
                },
                "ProductListingDetails": {
                    "EAN": "N/A"
                },
                "PictureDetails": {
                    "PictureURL": pic_object
                },
                "DispatchTimeMax": upload_data["user_info"]["max_dispatch_time"]
            }
        }

        if request["Item"]["ConditionID"] == "1000":    # If item is new no condition description is allowed
            del request["Item"]["ConditionDescription"]

        response = self.connections[site_num].execute("AddFixedPriceItem", request).dict()
        status = response["Ack"] if ("Ack" in response) else None

        if status == "Success":
            to_return = "Success"
        elif status in {"Warning", "Failure"}:
            to_return = f"{status}  ------  {response}"
        else:
            to_return = "No Response / Other Error \nLikely An Issue With Ebay Server Or Your Internet Connection\n"

        return f"{site_num}Listing {self.listing_number} Upload To {self.SITE_NAMES[site_num]}:  {to_return}"

    def upload_items(self, en_listings):
        self.items_thread = threading.Thread(target=self.upload_items_thread, args=(en_listings,))
        self.items_thread.start()

    def upload_items_thread(self, en_listings):
        print("Translating...")
        listings = self.translator.translate(en_listings)

        print("Uploading...")
        self.display = self.UploadDisplay(listings, self.ui, self)

        self.length = len(listings)
        self.listing_number = 1

        account_data = self.accounts.accounts_choice
        for item_batch in listings:
            item = item_batch[1] if (len(item_batch) > 1) else item_batch[0]
            if self.stop_upload:
                self.stop_upload = False
                tools.display_error(f"Upload stopped on this SKU: {item['SKU']}")
                break

            if account_data["default_uploads"]:
                upload_countries = account_data["default_uploads"]
                website = False
            else:
                upload_countries = self.item_type.upload_data["upload_to"]
                website = self.upload_mode.upload_state[7] and "SQL" in upload_countries

            fast_images = self.upload_mode.upload_state[8]
            ebay_images = any(self.upload_mode.upload_state[:6])
            if ebay_images:
                item_pic_object = self.make_pic_object(item["Path"])
                if not item_pic_object:
                    self.display.set_item_status(self.listing_number - 1, "Failure")
                    continue
            if website:
                if fast_images:
                    item_pic_object = self.website_upload_pics(item["Path"], item["SKU"], item["Title"])
                    if not item_pic_object:
                        continue
                else:
                    self.website_upload_pics(item["Path"], item["SKU"], item["Title"])

            feedback = []
            with ThreadPoolExecutor() as executor:
                if ebay_images:
                    for site_num,details in enumerate(item_batch):
                        if self.upload_mode.OPTIONS[site_num] in upload_countries and details:
                            feedback.append(executor.submit(self.send_item, site_num, details, item_pic_object))
                if website:
                    feedback.append(executor.submit(self.upload_to_database, item))

            final_feedback = [fd.result() for fd in feedback]
            final_feedback.sort(key=lambda x: x[0])
            final_feedback = [ff[1:] for ff in final_feedback]

            worst_error = "Success"
            for reply in final_feedback:
                if "Failure" in reply:
                    worst_error = "Failure"
                    self.display.push_error(reply)
                elif "Warning" in reply and worst_error != "Failure":
                    worst_error = "Warning"
                    self.display.push_error(reply)
                elif worst_error != "Warning" and worst_error != "Failure":
                    worst_error = "Success"

            self.display.set_item_status(self.listing_number - 1, worst_error)
            self.ui.window.update()
            self.listing_number += 1

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
        for i,item in enumerate(self.ui.item_specifics):
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
            for i,item in enumerate(self.ui.item_specifics):
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

