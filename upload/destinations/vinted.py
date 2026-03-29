from __future__ import annotations

import html
import re
import time
import random
import threading
import pathlib

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from upload.destinations.base import Destination
from upload.models.upload_result import UploadResult, UploadStatus


_FIT_TO_CATEGORY = {
    "Slim": "Slim fit jeans",
}
_CONDITION_MAP = {
    "1000": "New with tags",
    "2990": "Very good",
    "3000": "Good",
}


def _chrome_major_version() -> int | None:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        return int(version.split(".")[0])
    except Exception:
        return None




def _strip_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return ' '.join(text.split())


def _xpath_str(text: str) -> str:
    """Return an XPath string literal that safely handles single quotes (e.g. Levi's)."""
    if "'" not in text:
        return f"'{text}'"
    parts = text.split("'")
    tokens = []
    for i, part in enumerate(parts):
        if part:
            tokens.append(f"'{part}'")
        if i < len(parts) - 1:
            tokens.append('"\'"')
    return "concat(" + ", ".join(tokens) + ")"


def _human_delay(low=0.4, high=1.4):
    time.sleep(random.uniform(low, high))


class VintedDestination(Destination):
    """Uploads items to Vinted via browser automation (undetected-chromedriver).

    The Chrome session is persistent: the user logs in once and the profile
    is reused on subsequent runs.  All uploads are serialised with a lock
    because a single driver instance cannot be driven concurrently.

    To start a session for the first time, call ensure_browser() and log in
    to Vinted in the opened browser before triggering any uploads.
    """

    _SELL_URL = "https://www.vinted.co.uk/items/new"

    def __init__(self, upload_config):
        self._profile_dir = upload_config.vinted_profile_dir
        self._driver = None
        self._display = None
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "Vinted"

    @property
    def label(self) -> str:
        return "Vinted"

    @property
    def fail_on_image_error(self) -> bool:
        return False

    def ensure_browser(self):
        """Start the Chrome browser if it is not already running."""
        if self._driver is None:
            profile_path = pathlib.Path(self._profile_dir).resolve()
            profile_path.mkdir(parents=True, exist_ok=True)
            options = uc.ChromeOptions()
            options.add_argument(f"--user-data-dir={profile_path}")
            self._driver = uc.Chrome(options=options, version_main=_chrome_major_version())
            self._driver.get(self._SELL_URL)

    def upload_images(self, paths: str, sku: str, title: str, display) -> list | None:
        """Vinted images are uploaded as local files inside upload_item.
        This just parses the paths so upload_item can pass them to the file input."""
        self._display = display
        path_list = [p for p in paths.split(";") if p]
        return path_list or None

    def upload_item(self, item_batch, images: list | None, listing_number: int) -> UploadResult:
        item = item_batch.default
        with self._lock:
            try:
                return self._do_upload(item, images)
            except Exception as e:
                return UploadResult(UploadStatus.FAILURE, message=f"Vinted: {e}")

    def _do_upload(self, item, images: list | None) -> UploadResult:
        self.ensure_browser()
        driver = self._driver
        wait = WebDriverWait(driver, 20)

        driver.get(self._SELL_URL)
        _human_delay(1.5, 3.0)

        self._dismiss_cookies(driver)

        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='add-photos-input']")
            ))
        except TimeoutException:
            if self._display:
                self._display.push_error("Vinted: not logged in — please log in in the browser window, upload will resume automatically", "")
            self._dismiss_cookies(driver)
            WebDriverWait(driver, 600).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='add-photos-input']")
            ))
            _human_delay(1.0, 2.0)
            self._dismiss_cookies(driver)

        self._upload_photos(driver, wait, images[::-1])
        self._fill_text(driver, wait, "[data-testid='title--input']", f"{item.title.title()} ({item.sku})")
        self._fill_textarea(driver, wait, "[data-testid='description--input']", _strip_html(item.description))
        self._select_category(driver, wait, item)
        self._select_dropdown_option(driver, wait, "[data-testid='brand-select-dropdown-input']",
                                     item["IS_Brand"])
        self._select_dropdown_option(driver, wait, "[data-testid='category-condition-single-list-input']",
                                     _CONDITION_MAP.get(item.ebay_condition, "Good"))
        self._select_dropdown_option(driver, wait, "[data-testid='size-select-dropdown-input']",
                                     "W" + item["IS_Size"])
        self._select_dropdown_option(driver, wait, "[data-testid='color-select-dropdown-input']",
                                     item["IS_Colour"])
        self._select_dropdown_option(driver, wait, "[data-testid='category-material-multi-list-input']",
                                     "Denim")
        self._fill_text(driver, wait, "[data-testid='price-input--input']", str(item.price))

        _human_delay(0.8, 1.5)
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-testid='upload-form-save-button']")
        )).click()
        _human_delay(2.0, 4.0)

        if "items/new" not in self._driver.current_url:
            return UploadResult(UploadStatus.SUCCESS, message=f"Vinted: {item.sku} uploaded")
        return UploadResult(UploadStatus.FAILURE,
                            message="Vinted: page did not navigate after submit — check browser")

    def _dismiss_cookies(self, driver):
        """Dismiss the cookie consent banner if present. Silently ignored if absent."""
        try:
            banner = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                (By.XPATH,
                 "//*[@id='onetrust-accept-btn-handler'] | "
                 "//button[contains(translate(normalize-space(),'ACEPT','acept'),'accept all')]  | "
                 "//button[contains(translate(normalize-space(),'ACEPT','acept'),'accept cookies')] | "
                 "//button[normalize-space()='Agree'] | "
                 "//button[normalize-space()='I agree'] | "
                 "//button[normalize-space()='OK']")
            ))
            banner.click()
            _human_delay(0.5, 1.0)
        except Exception:
            pass

    def _upload_photos(self, driver, wait, images: list | None):
        if not images:
            return
        file_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-testid='add-photos-input']")
        ))
        driver.execute_script("arguments[0].style.display = 'block';", file_input)
        file_input.send_keys("\n".join(str(pathlib.Path(p).resolve()) for p in images))
        _human_delay(1.0, 2.0)

    def _fill_text(self, driver, wait, selector: str, text: str):
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        _human_delay(0.2, 0.4)
        driver.execute_script("arguments[0].click();", element)
        _human_delay(0.2, 0.5)
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.04, 0.12))

    def _fill_textarea(self, driver, wait, selector: str, text: str):
        self._fill_text(driver, wait, selector, text)

    def _select_category(self, driver, wait, item):
        """Open the category modal and navigate the hierarchy by scrolling and clicking."""
        fit = item["IS_Fit"]
        category_label = _FIT_TO_CATEGORY.get(fit, "Straight fit jeans")
        department = "Men" if item["IS_Department"] == "Men" else "Women"

        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-testid='catalog-select-dropdown-input']")
        )).click()
        _human_delay(0.8, 1.5)

        for label in (department, "Clothing", "Jeans", category_label):
            s = _xpath_str(label)
            btn = wait.until(EC.presence_of_element_located((By.XPATH,
                f"//div[@data-testid='catalog-select-dropdown-content']"
                f"//div[@role='button'][.//*[normalize-space()={s}]]"
            )))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            _human_delay(0.2, 0.4)
            btn.click()
            _human_delay(0.8, 1.5)

    def _select_via_search(self, driver, wait, trigger_selector: str, search_input_id: str, search_text: str):
        """Open a search-based modal dropdown, type the search term, scroll to and click the result."""
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, trigger_selector))).click()
        _human_delay(0.8, 1.5)

        search_input = wait.until(EC.element_to_be_clickable((By.ID, search_input_id)))
        for char in search_text:
            search_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.12))
        _human_delay(0.8, 1.5)

        self._scroll_and_click(driver, wait, search_text)

    def _select_dropdown_option(self, driver, wait, trigger_selector: str, option_text: str):
        """Open a dropdown, scroll to the matching option, and click it."""
        trigger = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, trigger_selector)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
        _human_delay(0.3, 0.6)
        driver.execute_script("arguments[0].click();", trigger)
        _human_delay(0.8, 1.5)
        self._scroll_and_click(driver, wait, option_text)
        _human_delay(0.5, 1.0)

    def _scroll_and_click(self, driver, wait, text: str, extra: str = ""):
        """Find an element by visible text, scroll it into view, and click it.
        extra: optional XPath prefix to scope the search (e.g. '//li[@role=\"tab\"]')."""
        prefix = extra or "//*"
        s = _xpath_str(text)
        element = wait.until(EC.presence_of_element_located((By.XPATH,
            f"{prefix}[normalize-space()={s}] | "
            f"{prefix}[.//span[normalize-space()={s}]] | "
            f"{prefix}[.//button[normalize-space()={s}]]"
        )))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        _human_delay(0.2, 0.4)
        element.click()
