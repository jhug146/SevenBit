"""
SevenBit v10
Able to upload to lovedjeans website
JSON file containing upload and translation data
"""
import tkinter as tk
from tkinter import messagebox

from state import ItemType, UploadMode, ItemList
from upload import Upload, EbayTranslator, UploadCallbacks
from ui import UploadDisplay, display_error
from download import GetItems
from ui.main_window import UI
from ui.utils import import_file
from ui.account_dialog import AccountDialog
from ui.item_type_dialog import ItemTypeDialog
from ui.download_dialog import DownloadDialog
from ui.upload_mode_dialog import UploadModeDialog
from upload.destinations import EbayImageStore, EbaySiteDestination, WebsiteDestination

import multiprocessing
import functools


try:
    item_type = ItemType()
except KeyError as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Configuration Error", str(e))
    raise SystemExit
upload_changer = UploadMode(item_type.upload, EbaySiteDestination.LABELS, EbaySiteDestination.OPTION_KEYS)
item_list = ItemList()
ui = UI(item_type.upload, item_list)
ui.update_title(item_type.accounts)
translator = EbayTranslator(item_type.translation, upload_changer)

ebay_image_store = EbayImageStore(item_type.accounts, item_type.upload, upload_changer)
website_dest = WebsiteDestination(item_type.upload)

destinations = [
    EbaySiteDestination(0, item_type.accounts, item_type.upload, ebay_image_store),  # US
    EbaySiteDestination(1, item_type.accounts, item_type.upload, ebay_image_store),  # UK
    EbaySiteDestination(2, item_type.accounts, item_type.upload, ebay_image_store),  # Australia
    EbaySiteDestination(3, item_type.accounts, item_type.upload, ebay_image_store),  # France
    EbaySiteDestination(4, item_type.accounts, item_type.upload, ebay_image_store),  # Germany
    EbaySiteDestination(5, item_type.accounts, item_type.upload, ebay_image_store),  # Italy
    EbaySiteDestination(6, item_type.accounts, item_type.upload, ebay_image_store),  # Spain
    website_dest,
]

# When fast_images is on, eBay listings use website-hosted image URLs.
# The website dest's upload_images already caches per SKU, so even though
# both the EbayImageStore (via fast_source) and the website dest itself call
# upload_images in the upload loop, only one real upload to the website occurs.
ebay_image_store.set_fast_source(website_dest.upload_images)

upload_changer.register(destinations)

make_display = lambda listings, upload: UploadDisplay(listings, ui, upload)

upload_callbacks = UploadCallbacks(
    on_validation_error=ui.outline_item,
    on_request_options=ui.get_options,
    on_tick=ui.window.update,
    on_error=display_error,
)
upload = Upload(
    item_type.accounts, translator, make_display, upload_changer, item_type.upload, destinations, item_list,
    upload_callbacks,
)
item_type.accounts.set_upload_attr(upload)
ui.set_upload_attr(upload)
get_items = GetItems(item_type.accounts, item_type.download, upload_changer, on_error=display_error)

account_dialog = AccountDialog(item_type.accounts, on_success=lambda: ui.update_title(item_type.accounts))
item_type_dialog = ItemTypeDialog(item_type, on_success=lambda: ui.update_title(item_type.accounts))
download_dialog = DownloadDialog(ui.window, get_items)
upload_mode_dialog = UploadModeDialog(upload_changer, item_type.accounts)

ui.init_buttons((
    functools.partial(import_file, ui),
    upload.request_upload,
    download_dialog.show,
    account_dialog.show,
    item_type_dialog.show,
    upload_mode_dialog.show,
    functools.partial(ui.update_title, item_type.accounts)
))

multiprocessing.freeze_support()   # Fixes issues with threading in the .exe file
ui.window.mainloop()
