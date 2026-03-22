from ebaysdk.trading import Connection as TradingConnection
import ebaysdk.exception

from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class EbayDestination:
    """Handles all eBay image hosting and per-region item uploads."""

    SITE_ABBRS = ("US", "UK", "Australia", "France", "Germany", "Italy", "Spain")
    SITE_IDS   = ("0",  "3",  "15",        "71",     "77",      "101",   "186")
    SITE_NAMES = ("ebay.com", "ebay.co.uk", "ebay.com.au", "ebay.fr", "ebay.de", "ebay.it", "ebay.es")
    SITE_CURRS = ("USD", "GBP", "AUD", "EUR", "EUR", "EUR", "EUR")
    MAX_RETRIES = 3

    def __init__(self, accounts, item_type, upload_mode):
        self.accounts = accounts
        self.item_type = item_type
        self.upload_mode = upload_mode
        self.update_connections()

    def update_connections(self):
        self.connections = []
        acc = self.accounts.accounts_choice["credentials"]
        for siteID in self.SITE_IDS:
            self.connections.append(TradingConnection(
                config_file=None,
                siteid=siteID,
                devid=acc["devid"],
                certid=acc["certid"],
                token=acc["token"],
                appid=acc["appid"],
                domain="api.ebay.com",
                debug=False
            ))

    def upload_images(self, paths: str, sku: str, display) -> list | None:
        """Upload images to eBay hosting. Returns list of URLs or None on failure."""
        path_list = paths.split(";")
        if path_list[-1] == "":
            path_list.pop()

        is_urls = True
        for path in path_list:
            if "http" not in path:
                is_urls = False
                break

        if is_urls:
            return path_list

        url_response = []
        with ThreadPoolExecutor(max_workers=12) as executor:
            urls = []
            for i, path in enumerate(path_list):
                url_response.append(executor.submit(self._upload_pic, path, i, sku, display))
                time.sleep(0.5)

            for ur in as_completed(url_response):
                result = ur.result()
                if result:
                    urls.append(result)

        print(urls)
        for url in urls:
            if "FailurePhotos" in url:
                return None

        urls.sort(key=lambda x: x[:2])
        urls = [u.lstrip("0123456789") for u in urls]
        return urls

    def _upload_pic(self, path, pic_id, sku, display):
        image_data = open(path, "rb").read()
        files = {"file": ("EbayImage", image_data)}
        attempts = 0
        str_pic_id = ("0" + str(pic_id)) if pic_id < 10 else str(pic_id)
        while attempts < self.MAX_RETRIES:
            attempts += 1
            if attempts == self.MAX_RETRIES:
                display.push_error("Exceeded max retries in uploading images to eBay, unsure why, contact James", sku)
                return str_pic_id + "FailurePhotos"
            try:
                acc = self.accounts.accounts_choice["credentials"]
                connection = TradingConnection(config_file=None, siteid="3", devid=acc["devid"], certid=acc["certid"], token=acc["token"], appid=acc["appid"], domain="api.ebay.com", debug=False)
                response = connection.execute("UploadSiteHostedPictures", self.item_type.upload_data["pictureData"], files=files)
                if "Ack" not in response.dict():
                    display.push_error(response.dict(), sku)
                    continue
                elif response.dict()["Ack"] == "Failure":
                    display.push_error(response.dict()["Errors"], sku)
                    continue
                break
            except Exception as error:
                display.push_error(error, sku)

        try:
            return str_pic_id + response.dict()["SiteHostedPictureDetails"]["PictureSetMember"][0]["MemberURL"]
        except KeyError as key_error:
            display.push_error(key_error, sku)
            return str_pic_id + "FailurePhotos"

    def send_item(self, site_num, details, pic_object, listing_number, display):
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

        try:
            response = self.connections[site_num].execute("AddFixedPriceItem", request).dict()
            status = response["Ack"] if ("Ack" in response) else None

            if status == "Success":
                to_return = "Success"
            elif status in {"Warning", "Failure"}:
                to_return = f"Ebay Upload  ---  {status}  ----  {response}"
            else:
                to_return = "No Response / Other Error \nLikely An Issue With Ebay Server Or Your Internet Connection\n"

            return f"{site_num}Listing {listing_number} Upload To {self.SITE_NAMES[site_num]}:  {to_return}"
        except ebaysdk.exception.ConnectionError as error:
            if "Duplicate" in str(error):
                return f"{site_num}Failure - Item is a duplicate"
            return f"{site_num}Failure - {error}"
