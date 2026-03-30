from __future__ import annotations

from ebaysdk.trading import Connection as TradingConnection
import ebaysdk.exception

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time

from upload.destinations.image_store import ImageStore
from upload.destinations.base import Destination
from upload.models.upload_result import UploadResult, ImageUploadResult, UploadStatus


@dataclass(frozen=True)
class SiteInfo:
    abbr: str
    id: str
    name: str
    currency: str
    option_key: str
    label: str

SITES = (
    SiteInfo("US",        "0",   "ebay.com",    "USD", "US",  "US" ),
    SiteInfo("UK",        "3",   "ebay.co.uk",  "GBP", "UK",  "UK" ),
    SiteInfo("Australia", "15",  "ebay.com.au", "AUD", "AUS", "AUS"),
    SiteInfo("France",    "71",  "ebay.fr",     "EUR", "FR",  "FRA"),
    SiteInfo("Germany",   "77",  "ebay.de",     "EUR", "DE",  "GER"),
    SiteInfo("Italy",     "101", "ebay.it",     "EUR", "IT",  "ITA"),
    SiteInfo("Spain",     "186", "ebay.es",     "EUR", "ES",  "SPA"),
)


class EbayImageStore:
    """Uploads images to eBay hosting once per SKU, thread-safely caching the result.

    All EbaySiteDestination instances for the same item share one EbayImageStore,
    so images are uploaded exactly once no matter how many regional sites are enabled.

    When upload_mode.fast_images is True, delegates to a website destination's
    upload_images instead of uploading to eBay. The website destination has its own
    ImageStore, so that path is also deduplicated.
    """

    MAX_RETRIES = 3

    def __init__(self, accounts, upload_config, upload_mode):
        self.accounts = accounts
        self.upload_config = upload_config
        self.upload_mode = upload_mode
        self._image_store = ImageStore()
        self._fast_source = None

    def set_fast_source(self, fast_source_fn):
        """Set the callable used instead of eBay hosting when fast_images is on.
        Should be website_dest.upload_images — that function already caches its result,
        so calling it multiple times for the same SKU only uploads once."""
        self._fast_source = fast_source_fn

    def get_images(self, paths: str, sku: str, title: str, display) -> list | None:
        if self.upload_mode.fast_images and self._fast_source:
            return self._fast_source(paths, sku, title, display)
        return self._image_store.get(sku, self._do_upload, paths, sku, display)

    def clear(self, sku: str):
        self._image_store.clear(sku)

    def _do_upload(self, paths: str, sku: str, display) -> list | None:
        path_list = paths.split(";")
        if path_list[-1] == "":
            path_list.pop()

        if all("http" in path for path in path_list):
            return path_list

        futures = []
        with ThreadPoolExecutor(max_workers=12) as executor:
            for i, path in enumerate(path_list):
                futures.append(executor.submit(self._upload_pic, path, i, sku, display))
                time.sleep(0.5)

        pic_results = [f.result() for f in as_completed(futures)]

        if any(r.status == UploadStatus.FAILURE for r in pic_results):
            return None

        pic_results.sort(key=lambda r: r.pic_id)
        return [r.url for r in pic_results]

    def _upload_pic(self, path, pic_id, sku, display) -> ImageUploadResult:
        with open(path, "rb") as f:
            image_data = f.read()
        files = {"file": ("EbayImage", image_data)}
        attempts = 0
        while attempts < self.MAX_RETRIES:
            attempts += 1
            try:
                connection = TradingConnection(config_file=None, siteid="3", devid=self.accounts.devid, certid=self.accounts.certid, token=self.accounts.token, appid=self.accounts.appid, domain="api.ebay.com", debug=False)
                response = connection.execute("UploadSiteHostedPictures", self.upload_config.picture_data, files=files).dict()
                if "Ack" not in response:
                    display.push_error(response, sku)
                    continue
                elif response["Ack"] == "Failure":
                    display.push_error(response["Errors"], sku)
                    continue
                break
            except Exception as error:
                display.push_error(error, sku)
        else:
            display.push_error("Exceeded max retries in uploading images to eBay, unsure why, contact James", sku)
            return ImageUploadResult(UploadStatus.FAILURE, pic_id)

        try:
            url = response["SiteHostedPictureDetails"]["PictureSetMember"][0]["MemberURL"]
            return ImageUploadResult(UploadStatus.SUCCESS, pic_id, url)
        except KeyError as key_error:
            display.push_error(key_error, sku)
            return ImageUploadResult(UploadStatus.FAILURE, pic_id)


class EbaySiteDestination(Destination):
    """Handles item upload to one eBay regional site.

    Seven of these are constructed (one per region), all sharing one EbayImageStore.
    The image store ensures only one eBay image upload happens per item regardless
    of how many regional sites are enabled.
    """

    def __init__(self, site_num: int, accounts, upload_config, image_store: EbayImageStore):
        self.site_num = site_num
        self.site = SITES[site_num]
        self.accounts = accounts
        self.upload_config = upload_config
        self.image_store = image_store
        self.update_connection()

    @property
    def name(self) -> str:
        return self.site.option_key

    @property
    def label(self) -> str:
        return self.site.label

    def has_data(self, item_batch) -> bool:
        return self.site_num < len(item_batch) and bool(item_batch[self.site_num])

    def clear_image_cache(self, sku: str):
        self.image_store.clear(sku)

    def update_connection(self):
        self.connection = TradingConnection(
            config_file=None,
            siteid=self.site.id,
            devid=self.accounts.devid,
            certid=self.accounts.certid,
            token=self.accounts.token,
            appid=self.accounts.appid,
            domain="api.ebay.com",
            debug=False
        )

    def upload_images(self, paths: str, sku: str, title: str, display) -> list | None:
        return self.image_store.get_images(paths, sku, title, display)

    def upload_item(self, item_batch, images: list | None, listing_number: int) -> UploadResult:
        details = item_batch[self.site_num]

        policies = self.accounts.policies(self.upload_config.name)

        item_specific_list = []
        for detail in details.specifics:
            prefix, suffix = detail[:3], detail[3:]
            if prefix != "IS_":
                continue
            if self.upload_config.translate_headers:
                item_specific_list.append({
                    "Name": self.upload_config.is_names[suffix][self.site_num],
                    "Value": details.specifics[detail]
                })
            elif details.specifics[detail]:
                item_specific_list.append({
                    "Name": suffix,
                    "Value": details.specifics[detail]
                })

        html = details.html.replace("&nbsp;", "")

        if not policies["payment"][self.site_num]:
            return UploadResult(UploadStatus.FAILURE, message="You haven't specified a payment policy number for all the sites you're attempting to upload to on this account")

        payment_id = policies["payment"][self.site_num]
        shipping_id = policies["shipping"][self.site_num]
        returns_id = policies["returns"][self.site_num]

        store_category = self.accounts.store_category
        request = {
            "Item": {
                "Title": details.title,
                "SKU": details.sku,
                "Description": f"<![CDATA[{html}]]>",
                "ConditionDescription": details.condition_description,
                "Country": self.upload_config.country,
                "Location": self.upload_config.country,
                "Site": self.site.abbr,
                "SiteId": self.site.id,
                "Currency": self.site.currency,
                "ConditionID": details.ebay_condition,
                "PrimaryCategory": {
                    "CategoryID": self.upload_config.category_id_map[item_batch.default["IS_Department"]]
                },
                "ListingDuration": "GTC",
                "StartPrice": details.price,
                "SellerProfiles": {
                    "SellerPaymentProfile":  {"PaymentProfileID":  payment_id},
                    "SellerShippingProfile": {"ShippingProfileID": shipping_id},
                    "SellerReturnProfile":   {"ReturnProfileID":   returns_id}
                },
                "SellerContactDetails": {
                    "County": self.upload_config.county
                },
                "PostalCode": self.upload_config.postcode,
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
                    "PictureURL": images
                },
                "DispatchTimeMax": self.upload_config.max_dispatch_time
            }
        }

        if request["Item"]["ConditionID"] == "1000":
            del request["Item"]["ConditionDescription"]

        site_label = f"Listing {listing_number} Upload To {self.site.name}"
        try:
            response = self.connection.execute("AddFixedPriceItem", request).dict()
            ebay_status = response["Ack"] if ("Ack" in response) else None

            if ebay_status == "Success":
                return UploadResult(UploadStatus.SUCCESS, message=f"{site_label}: Success")
            elif ebay_status == "Warning":
                return UploadResult(UploadStatus.WARNING, message=f"{site_label}: Ebay Upload  ---  Warning  ----  {response}")
            elif ebay_status == "Failure":
                return UploadResult(UploadStatus.FAILURE, message=f"{site_label}: Ebay Upload  ---  Failure  ----  {response}")
            else:
                return UploadResult(UploadStatus.FAILURE, message=f"{site_label}: No Response / Other Error\nLikely An Issue With Ebay Server Or Your Internet Connection\n")
        except ebaysdk.exception.ConnectionError as error:
            if "Duplicate" in str(error):
                return UploadResult(UploadStatus.FAILURE, message="Item is a duplicate")
            return UploadResult(UploadStatus.FAILURE, message=str(error))
