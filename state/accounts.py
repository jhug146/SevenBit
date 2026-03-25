from state._json import load_json_file


class Accounts:
    def __init__(self, item_type):
        self.item_type = item_type
        self.account_data = load_json_file("user/accounts.json")
        self.accounts_choice = self.account_data[self.account_data["default"]]

    def set_upload_attr(self, upload):
        self.upload = upload

    def switch_account(self, name):
        try:
            self.accounts_choice = self.account_data[name]
            self.upload.update_connections()
            return True
        except (ValueError, KeyError):
            return False
