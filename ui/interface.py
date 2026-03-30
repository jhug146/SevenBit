from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class AppActions:
    import_file: Callable
    upload: Callable
    download: Callable
    switch_account: Callable
    switch_item_type: Callable
    change_upload_mode: Callable
    get_status: Callable


class BaseUI(ABC):

    @abstractmethod
    def show_items(self): ...

    @abstractmethod
    def outline_item(self, items, red): ...

    @abstractmethod
    def get_options(self, upload_obj, start=""): ...

    @abstractmethod
    def update_title(self, accounts): ...

    @abstractmethod
    def set_upload_attr(self, upload): ...

    @abstractmethod
    def show_error(self, message): ...

    @abstractmethod
    def tick(self): ...

    @abstractmethod
    def run(self): ...

    @abstractmethod
    def save_item(self, n, changes: dict): ...

    @abstractmethod
    def register_actions(self, actions: AppActions): ...


class BaseUploadDisplay(ABC):

    @abstractmethod
    def set_item_status(self, item_num, status): ...

    @abstractmethod
    def push_error(self, message, sku): ...
