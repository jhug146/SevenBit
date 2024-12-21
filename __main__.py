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
from tools import UI, import_file
from upload_mode import UploadMode

import multiprocessing
import functools


item_type = ItemType()
upload_changer = UploadMode(item_type)
item_type.pass_upload(upload_changer)
ui = UI(item_type)
accounts = Accounts(ui, item_type)
translator = EbayTranslator(item_type, upload_changer)
ebay_upload = EbayUpload(accounts, ui, translator, UploadDisplay, upload_changer, item_type)
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
    upload_changer.change_mode
))

multiprocessing.freeze_support()   # Fixes issues with threading in the .exe file
ui.window.mainloop()
