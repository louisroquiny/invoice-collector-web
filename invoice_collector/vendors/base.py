from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from invoice_collector.models import CollectResult
from invoice_collector.utils import sanitize_filename, unique_path


def wait_for_manual_login(page: Page, vendor: str, assume_logged_in: bool) -> None:
    if assume_logged_in:
        return
    print(
        f"\n[{vendor}] Si le site demande une connexion, un SSO, un MFA ou une vérification, "
        "terminez-le dans la fenêtre Chrome."
    )
    input("Quand la session est prête, appuyez sur Entrée pour continuer...")


def capture_user_download(
    page: Page,
    vendor: str,
    period: str,
    download_root: Path,
    timeout_ms: int = 300_000,
) -> CollectResult:
    """Capture le prochain téléchargement déclenché manuellement par l'utilisateur.

    Cette fonction est volontairement assistée: l'utilisateur navigue jusqu'à la bonne facture
    dans le portail fournisseur, puis le script se met en écoute avant que l'utilisateur clique
    sur le bouton Télécharger. C'est beaucoup plus robuste pour les portails avec MFA, CAPTCHA,
    SSO ou interfaces qui changent souvent.
    """
    vendor_dir = download_root / vendor / period
    vendor_dir.mkdir(parents=True, exist_ok=True)

    print("")
    print(f"[{vendor}] Mode capture de téléchargement")
    print(f"1. Dans Chrome, allez jusqu'à la facture {period}.")
    print("2. Préparez-vous à cliquer sur le bouton Télécharger / Download / PDF.")
    print("3. Revenez dans PowerShell et appuyez sur Entrée.")
    print("4. Ensuite seulement, cliquez sur Télécharger dans Chrome.")
    print("")

    try:
        with page.expect_download(timeout=timeout_ms) as download_info:
            input("Appuyez sur Entrée ici, puis cliquez sur Télécharger dans Chrome... ")

        download = download_info.value
        filename = sanitize_filename(download.suggested_filename or f"{vendor}_{period}.pdf")
        output_path = unique_path(vendor_dir / filename)
        download.save_as(output_path)
        return CollectResult.found(
            vendor,
            period,
            output_path,
            message=f"Facture capturée et enregistrée: {output_path}",
        )
    except PlaywrightTimeoutError:
        return CollectResult.error(
            vendor,
            period,
            "Aucun téléchargement détecté. Il faut appuyer sur Entrée dans PowerShell avant de cliquer sur Télécharger dans Chrome.",
        )
    except Exception as exc:  # noqa: BLE001
        return CollectResult.error(vendor, period, f"Téléchargement non capturé: {exc}")


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
