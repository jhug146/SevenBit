import functools

from state import ItemType, UploadMode
from upload.models import ItemList
from upload import Upload, EbayTranslator, UploadCallbacks
from ui.interface import AppActions
from ui.website.ui import DjangoUI, DjangoUploadDisplay
from ui.website.state import state
from download import GetItems
from upload.destinations import EbayImageStore, EbaySiteDestination, WebsiteDestination, VintedDestination, SITES


class WebApp:
    def __init__(self):
        item_type = ItemType()

        upload_changer = UploadMode(
            item_type.upload,
            [s.label for s in SITES],
            [s.option_key for s in SITES],
        )
        item_list = ItemList()

        ui = DjangoUI(item_type.upload, item_list)
        ui.update_title(item_type.accounts)

        translator = EbayTranslator(item_type.translation, upload_changer, item_type.accounts)

        ebay_image_store = EbayImageStore(item_type.accounts, item_type.upload, upload_changer)
        website_dest = WebsiteDestination(item_type.upload, item_type.accounts)
        vinted_dest = VintedDestination(item_type.upload)

        destinations = [
            EbaySiteDestination(0, item_type.accounts, item_type.upload, ebay_image_store),
            EbaySiteDestination(1, item_type.accounts, item_type.upload, ebay_image_store),
            EbaySiteDestination(2, item_type.accounts, item_type.upload, ebay_image_store),
            EbaySiteDestination(3, item_type.accounts, item_type.upload, ebay_image_store),
            EbaySiteDestination(4, item_type.accounts, item_type.upload, ebay_image_store),
            EbaySiteDestination(5, item_type.accounts, item_type.upload, ebay_image_store),
            EbaySiteDestination(6, item_type.accounts, item_type.upload, ebay_image_store),
            website_dest,
            vinted_dest,
        ]

        ebay_image_store.set_fast_source(website_dest.upload_images)
        upload_changer.register(destinations)

        make_display = lambda listings, upload: DjangoUploadDisplay(listings, upload)

        upload_callbacks = UploadCallbacks(
            on_validation_error=ui.outline_item,
            on_request_options=ui.get_options,
            on_tick=ui.tick,
            on_error=ui.show_error,
        )
        upload = Upload(
            item_type.accounts, translator, make_display, upload_changer,
            item_type.upload, destinations, item_list, upload_callbacks,
        )
        item_type.accounts.set_upload_attr(upload)
        ui.set_upload_attr(upload)

        get_items = GetItems(
            item_type.accounts, item_type.download, upload_changer,
            on_error=ui.show_error,
        )

        # Populate state so views can access all objects
        state.item_list = item_list
        state.upload_changer = upload_changer
        state.item_type = item_type
        state.get_items = get_items

        ui.register_actions(AppActions(
            import_file=lambda: None,           # handled directly by view
            upload=lambda: None,                # views call upload methods directly
            download=lambda: None,              # handled directly by view
            switch_account=item_type.accounts.switch_account,
            switch_item_type=item_type.get_info,
            change_upload_mode=lambda: None,    # handled directly by view
            get_status=functools.partial(ui.update_title, item_type.accounts),
        ))

        self.ui = ui

    def run(self):
        self.ui.run()
