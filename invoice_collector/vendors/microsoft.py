from pathlib import Path

from invoice_collector.browser import PersistentBrowser
from invoice_collector.models import CollectResult
from invoice_collector.vendors.base import save_first_matching_download, wait_for_manual_login

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
        page.goto(url, wait_until="networkidle")
        return save_first_matching_download(
            page=page,
            vendor=VENDOR,
            period=period,
            download_root=download_root,
            link_text_candidates=[period, period.replace("-", "/"), "Download", "Télécharger", "Invoice", "Facture"],
            fallback_message=f"Aucune facture Microsoft trouvée automatiquement pour {period}. Le portail Microsoft varie selon le type de compte.",
        )
