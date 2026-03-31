import os

from ui.interface import BaseUI, BaseUploadDisplay
from ui.website.state import state


class DjangoUI(BaseUI):

    def __init__(self, upload_config, item_list):
        self.upload_config = upload_config
        self.item_list = item_list

    def show_items(self):
        pass  # items page always renders from state

    def outline_item(self, items, red):
        state.outlined_items = items if isinstance(items, list) else [items]
        state.outlined_red = red

    def get_options(self, upload_obj, start=""):
        # Upload is started directly by views in web mode; this is a no-op
        pass

    def update_title(self, accounts):
        state.title = f"SevenBit — {accounts.name} — {self.upload_config.name}"

    def set_upload_attr(self, upload):
        state.upload = upload

    def show_error(self, message):
        state.sse_queue.put({"type": "error", "message": message})

    def tick(self):
        pass  # no Tkinter event loop needed

    def run(self):
        os.environ["DJANGO_SETTINGS_MODULE"] = "ui.website.settings"
        from django.core.management import execute_from_command_line
        execute_from_command_line(["manage.py", "runserver", "--noreload"])

    def save_item(self, n, changes: dict):
        for key, value in changes.items():
            self.item_list.items[n][key] = value

    def register_actions(self, actions):
        state.actions = actions


class DjangoUploadDisplay(BaseUploadDisplay):

    def __init__(self, listings, upload):
        self.listings = listings
        self.upload = upload
        state.upload_display = self
        # Clear stale events from any previous upload
        while not state.sse_queue.empty():
            try:
                state.sse_queue.get_nowait()
            except Exception:
                break
        # Queue init events so the browser table can be populated on connect
        for i, batch in enumerate(listings):
            state.sse_queue.put({
                "type": "init",
                "item_num": i,
                "title": batch.title,
                "sku": batch.sku,
            })

    def set_item_status(self, item_num, status):
        state.sse_queue.put({
            "type": "status",
            "item_num": item_num,
            "status": status.value,
        })

    def push_error(self, message, sku):
        state.sse_queue.put({
            "type": "log",
            "message": message,
            "sku": sku,
        })
