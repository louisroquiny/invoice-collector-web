from pathlib import Path

from invoice_collector.browser import PersistentBrowser
from invoice_collector.models import CollectResult
from invoice_collector.vendors.base import capture_user_download, wait_for_manual_login

VENDOR = "microsoft"
DEFAULT_URL = "https://admin.microsoft.com/Adminportal/Home#/billoverview/invoice-list"


def collect_invoice(
    period: str,
    download_root: Path,
    profiles_root: Path,
    headless: bool,
    assume_logged_in: bool,
    options: dict,
) -> CollectResult:
    url = options.get("url", DEFAULT_URL)
    with PersistentBrowser(VENDOR, profiles_root, headless=headless) as (_, _, page):
        page.goto(url, wait_until="domcontentloaded")
        wait_for_manual_login(page, VENDOR, assume_logged_in)
        return capture_user_download(page, VENDOR, period, download_root)
