from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from invoice_collector.models import CollectResult
from invoice_collector.utils import sanitize_filename, unique_path


def wait_for_manual_login(page: Page, vendor: str, assume_logged_in: bool) -> None:
    if assume_logged_in:
        return
    print(
        f"\n[{vendor}] Si le site demande une connexion, un SSO ou un MFA, "
        "terminez-le dans la fenêtre Chromium."
    )
    input("Quand la session est prête, appuyez sur Entrée pour continuer...")


def save_first_matching_download(
    page: Page,
    vendor: str,
    period: str,
    download_root: Path,
    link_text_candidates: list[str],
    fallback_message: str,
) -> CollectResult:
    vendor_dir = download_root / vendor / period
    vendor_dir.mkdir(parents=True, exist_ok=True)

    for text in link_text_candidates:
        try:
            locator = page.get_by_text(text, exact=False).first
            locator.wait_for(timeout=3000)
            with page.expect_download(timeout=10000) as download_info:
                locator.click()
            download = download_info.value
            filename = sanitize_filename(download.suggested_filename or f"{vendor}_{period}.pdf")
            output_path = unique_path(vendor_dir / filename)
            download.save_as(output_path)
            return CollectResult.found(vendor, period, output_path)
        except PlaywrightTimeoutError:
            continue
        except Exception as exc:  # noqa: BLE001
            return CollectResult.error(vendor, period, f"Téléchargement impossible: {exc}")

    return CollectResult.missing(vendor, period, fallback_message)
