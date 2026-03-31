from __future__ import annotations

import html
import re
import time
import random
import threading
import pathlib

from upload.destinations.sku_codec import encode_sku

import tempfile

from PIL import Image
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
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


def _vinted_price(item) -> str:
    return str(int((float(item.price) - 2.40) / 1.06))


def _build_vinted_title(item, sku_tag: str) -> str:
    tag_w = _get(item, "Tag W")
    tag_l = _get(item, "Tag L")
    size = f"{tag_w} x {tag_l}" if tag_w and tag_l else item["IS_Size"]
    model = item['IS_Model'].title()
    fit = item['IS_Fit'].title()
    colour = item['IS_Colour'].title()
    return f"{model} {fit} Jeans {size} {colour} #{sku_tag}"


_CONDITION_REWRITES = [
    # ── Main condition phrases ────────────────────────────────────────────────
    (re.compile(r"in very\s+good condition with no wear at the hems,?\s*please note that they have been taken up from their original length", re.I),
     "Very good condition — hems have been taken up from original length"),
    (re.compile(r"in good condition with no wear at the hems,?\s*please note that they have been taken up from their original length", re.I),
     "Good condition — hems have been taken up from original length"),
    (re.compile(r"in good condition apart from some wear on the seam between the legs", re.I),
     "Good condition with some inner seam wear"),
    (re.compile(r"in good very condition with a bit of wear at the hems", re.I),
     "Good condition with some hem wear"),
    (re.compile(r"in good condition with a bit of wear around the edges \(pictured\)", re.I),
     "Good condition — light edge wear visible in photos"),
    (re.compile(r"in good condition with no wear to the hems", re.I),
     "Good condition, hems intact"),
    (re.compile(r"in good condition with no wear at the hems", re.I),
     "Good condition, hems intact"),
    (re.compile(r"in reasonable condition with a bit of wear around the edges \(pictured\)", re.I),
     "Fair condition with some edge wear visible in photos"),
    (re.compile(r"in very\s+good condition", re.I),
     "Very good condition"),
    (re.compile(r"in good condition", re.I),
     "Good condition"),
    (re.compile(r"brand new with tags", re.I),
     "Brand new, tags still attached"),
    # ── Sizing notes ─────────────────────────────────────────────────────────
    (re.compile(r"these jeans do measure longer in the leg than the label suggests[^.]*\.?", re.I),
     "Leg measures longer than the label size"),
    (re.compile(r"these jeans do measure shorter in the leg than the label suggests[^.]*\.?", re.I),
     "Leg measures shorter than the label size"),
    (re.compile(r"these jeans do measure slightly bigger at the waist than the label suggests[^.]*\.?", re.I),
     "Waist measures slightly larger than the label size"),
    (re.compile(r"please note that they are\s+a bit bigger at the waist and longer in the leg[^.]*\.?", re.I),
     "Waist and leg both measure larger than the label"),
    (re.compile(r"please note that they are\s+a bit smaller at the waist and shorter in the leg[^.]*\.?", re.I),
     "Waist and leg both measure smaller than the label"),
    # ── Standalone notes ─────────────────────────────────────────────────────
    (re.compile(r"please note that they have been taken up from their original length\.?", re.I),
     "Hems have been taken up from original length"),
    (re.compile(r"please note that ther[ea]\s+r?e?\s+a few faint bleach marks on the l[eg]+s?\.?", re.I),
     "A few faint bleach marks on the legs"),
    (re.compile(r"quite a lightweight denim", re.I),
     "Lightweight denim"),
    (re.compile(r"very very dark blue almost black", re.I),
     "Very dark blue, almost black"),
    (re.compile(r"american sizing", re.I),
     "American sizing"),
    (re.compile(r"small for size,?\s*possibly a (W?\d+)", re.I),
     r"Comes up small — likely a \1"),
    (re.compile(r"big for size,?\s*possibly a (W?\d+)", re.I),
     r"Comes up large — likely a \1"),
    # ── Cleanup ──────────────────────────────────────────────────────────────
    (re.compile(r"\s*[--]\s*please see actual measurements?\.?", re.I), ""),
    (re.compile(r"\s*please see actual measurements?\.?", re.I), ""),
]


def _rewrite_condition(text: str) -> str:
    text = text.strip()
    for pattern, replacement in _CONDITION_REWRITES:
        text = pattern.sub(replacement, text)
    return text.strip()


def _get(item, key: str) -> str:
    try:
        return item[key] or ""
    except (KeyError, IndexError):
        return ""


def _to_cm(inches: str) -> str:
    try:
        return str(round(float(inches) * 2.54))
    except (ValueError, TypeError):
        return ""


def _build_vinted_description(item) -> str:
    model   = _get(item, "IS_Model")
    fit     = _get(item, "IS_Fit")
    colour  = _get(item, "IS_Colour")
    material = _get(item, "IS_Exact Material") or _get(item, "IS_Material")
    closure  = _get(item, "IS_Closure")
    wash     = _get(item, "IS_Fabric Wash")
    tag_w    = _get(item, "Tag W")
    tag_l    = _get(item, "Tag L")
    waist    = _get(item, "Waist")
    leg      = _get(item, "Inside Leg")
    out_leg  = _get(item, "Out. Leg")
    rise     = _get(item, "Rise")
    hem      = _get(item, "Hem")

    parts = []

    # Opening line
    parts.append(f"{model} {fit} {colour} Jeans.")

    parts.append(f" Measured waist size: {waist}\" ({_to_cm(waist)}cm)")
    parts.append(f" Measured inside leg: {leg}\" ({_to_cm(leg)}cm)")

    def _differs(a, b):
        def _num(v):
            return float(re.sub(r'^[^\d.]+', '', str(v).strip()))
        try:
            return abs(_num(a) - _num(b)) >= 0.5
        except (ValueError, TypeError):
            return False

    if (tag_w and waist and _differs(tag_w, waist)) or (tag_l and leg and _differs(tag_l, leg)):
        parts.append("*** Please note these jeans have been listed as the measured size for a better fit and this differs from the tag size ***")

    # Tag vs actual size
    if tag_w:
        line = f"Tag size: W{tag_w}"
        if tag_l:
            line += f" L{tag_l}"
        parts.append(line)

    # Additional measurements
    extras = []
    if out_leg:
        extras.append(f"outside leg {out_leg}\"")
    if rise:
        extras.append(f"rise {rise}\"")
    if hem:
        extras.append(f"hem {hem}\"")
    if extras:
        parts.append("Additional measurements: " + ", ".join(extras) + ".")

    # Condition notes
    conditions = [_rewrite_condition(c) for c in item.conditions if c and c.strip()]
    conditions = [c for c in conditions if c]
    if conditions:
        parts.append("Condition: " + " | ".join(conditions))

    # Details line
    details = []
    if material:
        details.append(f"Material: {material}")
    if closure:
        details.append(f"Fly: {closure}")
    if wash:
        details.append(f"Wash code: {wash}")
    if details:
        parts.append(" | ".join(details))

    return "\n\n".join(parts)


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


def _wander_mouse(driver):
    """Move the mouse to a few random nearby positions to simulate idle movement."""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        for _ in range(random.randint(2, 5)):
            x = random.randint(-150, 150)
            y = random.randint(-80, 80)
            ActionChains(driver).move_to_element_with_offset(body, x, y).perform()
            time.sleep(random.uniform(0.1, 0.35))
    except Exception:
        pass


def _perturb_image(path: str) -> str:
    """Return a temp copy of the image with imperceptible pixel noise to change its hash."""
    img = Image.open(path).convert("RGB")
    pixels = img.load()
    w, h = img.size
    for _ in range(max(1, int(w * h * 0.001))):
        x, y = random.randint(0, w - 1), random.randint(0, h - 1)
        r, g, b = pixels[x, y]
        channel = random.randint(0, 2)
        delta = random.choice([-1, 1])
        if channel == 0:
            r = max(0, min(255, r + delta))
        elif channel == 1:
            g = max(0, min(255, g + delta))
        else:
            b = max(0, min(255, b + delta))
        pixels[x, y] = (r, g, b)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    img.save(tmp_path, "JPEG", quality=95)
    return tmp_path


class VintedDestination(Destination):
    """Uploads items to Vinted via browser automation (undetected-chromedriver).

    The Chrome session is persistent: the user logs in once and the profile
    is reused on subsequent runs.  All uploads are serialised with a lock
    because a single driver instance cannot be driven concurrently.

    To start a session for the first time, call ensure_browser() and log in
    to Vinted in the opened browser before triggering any uploads.
    """

    _SELL_URL = "https://www.vinted.co.uk/items/new"
    _BROWSE_URLS = [
        "https://www.vinted.co.uk/",
        "https://www.vinted.co.uk/catalog?search_text=jeans",
        "https://www.vinted.co.uk/member/inbox",
    ]

    def __init__(self, upload_config):
        self._profile_dir = upload_config.vinted_profile_dir
        self._driver = None
        self._display = None
        self._lock = threading.Lock()
        self._upload_count = 0
        self._next_long_pause_at = random.randint(3, 6)

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
            options.add_argument("--start-maximized")
            options.add_argument("--window-size=1920,1080")
            self._driver = uc.Chrome(options=options, version_main=_chrome_major_version())
            _human_delay(1.5, 2.5)
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
                result = self._do_upload(item, images)
            except Exception as e:
                result = UploadResult(UploadStatus.FAILURE, message=f"Vinted: {e}")
            self._upload_count += 1
            if self._upload_count >= self._next_long_pause_at:
                _human_delay(300, 600)  # 5–10 min break every few items
                self._upload_count = 0
                self._next_long_pause_at = random.randint(3, 6)
            else:
                _human_delay(45, 150)
        return result

    def _do_upload(self, item, images: list | None) -> UploadResult:
        self.ensure_browser()
        driver = self._driver
        wait = WebDriverWait(driver, 20)

        driver.get(self._SELL_URL)
        _human_delay(1.5, 3.0)

        self._dismiss_cookies(driver)

        already_logged_in = True
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='add-photos-input']")
            ))
        except TimeoutException:
            already_logged_in = False
            if self._display:
                self._display.push_error("Vinted: not logged in — please log in in the browser window, upload will resume automatically", "")
            self._dismiss_cookies(driver)
            WebDriverWait(driver, 600).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='add-photos-input']")
            ))
            _human_delay(1.0, 2.0)
            self._dismiss_cookies(driver)

        if already_logged_in and random.random() < 0.4:
            driver.get(random.choice(self._BROWSE_URLS))
            _human_delay(4.0, 10.0)
            self._dismiss_cookies(driver)
            driver.get(self._SELL_URL)
            _human_delay(1.5, 3.0)

        temp_files = self._upload_photos(driver, wait, images[::-1])
        try:
            self._fill_text(driver, wait, "[data-testid='title--input']", _build_vinted_title(item, encode_sku(item.sku)))
            _wander_mouse(driver)
            self._fill_textarea(driver, wait, "[data-testid='description--input']", _build_vinted_description(item))
            _wander_mouse(driver)
            self._select_category(driver, wait, item)
            self._select_dropdown_option(driver, wait, "[data-testid='brand-select-dropdown-input']",
                                         item["IS_Brand"])
            _wander_mouse(driver)
            self._select_dropdown_option(driver, wait, "[data-testid='category-condition-single-list-input']",
                                         _CONDITION_MAP.get(item.ebay_condition, "Good"))
            self._select_dropdown_option(driver, wait, "[data-testid='size-select-dropdown-input']",
                                         "W" + item["IS_Size"])
            _wander_mouse(driver)
            colour_area = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='color-select-dropdown-input']")
            ))
            if item["IS_Colour"].lower() not in colour_area.text.lower():
                try:
                    self._select_dropdown_option(driver, wait, "[data-testid='color-select-dropdown-input']",
                                                 item["IS_Colour"])
                except TimeoutException:
                    pass
            try:
                self._select_dropdown_option(driver, wait, "[data-testid='category-material-multi-list-input']",
                                             "Denim")
            except TimeoutException:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                _human_delay(0.3, 0.6)
            self._fill_text(driver, wait, "[data-testid='price-input--input']", _vinted_price(item))

            _wander_mouse(driver)
            _human_delay(0.8, 1.5)
            save_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='upload-form-save-button']")
            ))
            ActionChains(driver).move_to_element(save_btn).perform()
            _human_delay(0.3, 0.8)
            ActionChains(driver).click(save_btn).perform()
            _human_delay(2.0, 4.0)

            if "items/new" not in self._driver.current_url:
                return UploadResult(UploadStatus.SUCCESS, message=f"Vinted: {item.sku} uploaded")
            return UploadResult(UploadStatus.FAILURE,
                                message="Vinted: page did not navigate after submit — check browser")
        finally:
            for f in temp_files:
                try:
                    pathlib.Path(f).unlink()
                except Exception:
                    pass

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

    def _upload_photos(self, driver, wait, images: list | None) -> list:
        """Upload perturbed copies of the images. Returns temp file paths for cleanup."""
        if not images:
            return []
        temp_paths = [_perturb_image(p) for p in images]
        file_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-testid='add-photos-input']")
        ))
        driver.execute_script("arguments[0].style.display = 'block';", file_input)
        file_input.send_keys("\n".join(str(pathlib.Path(p).resolve()) for p in temp_paths))
        _human_delay(1.0, 2.0)
        return temp_paths

    def _fill_text(self, driver, wait, selector: str, text: str):
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        ActionChains(driver).move_to_element(element).perform()
        _human_delay(0.2, 0.4)
        ActionChains(driver).click(element).perform()
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

        trigger = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-testid='catalog-select-dropdown-input']")
        ))
        ActionChains(driver).move_to_element(trigger).perform()
        _human_delay(0.3, 0.6)
        ActionChains(driver).click(trigger).perform()
        _human_delay(0.8, 1.5)

        for label in (department, "Clothing", "Jeans", category_label):
            s = _xpath_str(label)
            btn = wait.until(EC.presence_of_element_located((By.XPATH,
                f"//div[@data-testid='catalog-select-dropdown-content']"
                f"//div[@role='button'][.//*[normalize-space()={s}]]"
            )))
            ActionChains(driver).move_to_element(btn).perform()
            _human_delay(0.2, 0.4)
            ActionChains(driver).click(btn).perform()
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
        ActionChains(driver).move_to_element(trigger).perform()
        _human_delay(0.3, 0.6)
        ActionChains(driver).click(trigger).perform()
        _human_delay(0.8, 1.5)
        self._scroll_and_click(driver, wait, option_text)
        _human_delay(0.5, 1.0)

    def _scroll_and_click(self, driver, wait, text: str, extra: str = ""):
        """Find an element by visible text, scroll it into view, and click it.
        extra: optional XPath prefix to scope the search (e.g. '//li[@role=\"tab\"]').
        Matching is case-insensitive and whitespace-normalised."""
        prefix = extra or "//*"
        s = _xpath_str(text.strip().lower())
        _U = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        _l = "abcdefghijklmnopqrstuvwxyz"
        def _lc(expr):
            return f"translate(normalize-space({expr}),'{_U}','{_l}')"
        element = wait.until(EC.presence_of_element_located((By.XPATH,
            f"{prefix}[{_lc('.')}={s}] | "
            f"{prefix}[.//span[{_lc('.')}={s}]] | "
            f"{prefix}[.//button[{_lc('.')}={s}]]"
        )))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        _human_delay(0.2, 0.4)
        element.click()
