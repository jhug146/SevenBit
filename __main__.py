"""
SevenBit v10
Able to upload to lovedjeans website
JSON file containing upload and translation data
"""
from item_type import ItemType
from translation import EbayTranslator
from download import GetItems
from upload import EbayUpload
from accounts import Accounts
from upload_display import UploadDisplay
from ui.main_window import UI
from ui.utils import import_file
from upload_mode import UploadMode
from destinations import EbayImageStore, EbaySiteDestination, WebsiteDestination
from item_list import ItemList

import multiprocessing
import functools


item_type = ItemType()
upload_changer = UploadMode(item_type)
item_type.pass_upload(upload_changer)
item_list = ItemList()
ui = UI(item_type, item_list)
accounts = Accounts(ui, item_type)
translator = EbayTranslator(item_type, upload_changer)

ebay_image_store = EbayImageStore(accounts, item_type, upload_changer)
website_dest = WebsiteDestination(item_type)

destinations = [
    EbaySiteDestination(0, accounts, item_type, ebay_image_store),  # US
    EbaySiteDestination(1, accounts, item_type, ebay_image_store),  # UK
    EbaySiteDestination(2, accounts, item_type, ebay_image_store),  # Australia
    EbaySiteDestination(3, accounts, item_type, ebay_image_store),  # France
    EbaySiteDestination(4, accounts, item_type, ebay_image_store),  # Germany
    EbaySiteDestination(5, accounts, item_type, ebay_image_store),  # Italy
    EbaySiteDestination(6, accounts, item_type, ebay_image_store),  # Spain
    website_dest,
]

# When fast_images is on, eBay listings use website-hosted image URLs.
# The website dest's upload_images already caches per SKU, so even though
# both the EbayImageStore (via fast_source) and the website dest itself call
# upload_images in the upload loop, only one real upload to the website occurs.
ebay_image_store.set_fast_source(website_dest.upload_images)

upload_changer.register(destinations)

ebay_upload = EbayUpload(accounts, ui, translator, UploadDisplay, upload_changer, item_type, destinations, item_list)
accounts.set_upload_attr(ebay_upload)
item_type.set_accounts_attr(accounts)
ui.set_upload_attr(ebay_upload)
get_items = GetItems(accounts.accounts_choice, ui, item_type, upload_changer)

ui.init_buttons((
    functools.partial(import_file, ui),
    ebay_upload.confirm_upload,
    get_items.get_numbers,
    accounts.choose_account,
    item_type.edit,
    upload_changer.change_mode,
    functools.partial(ui.update_title, accounts)
))

multiprocessing.freeze_support()   # Fixes issues with threading in the .exe file
ui.window.mainloop()
