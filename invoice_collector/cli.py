import importlib
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from invoice_collector.config import load_config
from invoice_collector.models import CollectResult
from invoice_collector.report import write_manifest
from invoice_collector.utils import ensure_period

app = typer.Typer(help="Collecte semi-automatique de factures depuis des portails web.")
console = Console()

VENDOR_MODULES = {
    "microsoft": "invoice_collector.vendors.microsoft",
    "openai": "invoice_collector.vendors.openai",
    "google": "invoice_collector.vendors.google",
    "ovhcloud": "invoice_collector.vendors.ovhcloud",
    "adobe": "invoice_collector.vendors.adobe",
}


@app.command()
def collect(
    config: Path = typer.Option(Path("config.yaml"), "--config", "-c"),
    downloads: Path = typer.Option(Path("downloads"), "--downloads", "-d"),
    profiles: Path = typer.Option(Path("browser_profiles"), "--profiles", "-p"),
    manifest: Path = typer.Option(Path("reports/manifest.csv"), "--manifest", "-m"),
    vendor: str | None = typer.Option(
        None,
        "--vendor",
        "-v",
        help="Limiter la collecte à un fournisseur: microsoft, openai, google, ovhcloud ou adobe.",
    ),
    headless: bool = typer.Option(False, "--headless", help="À éviter au début à cause du MFA."),
    assume_logged_in: bool = typer.Option(
        False,
        "--assume-logged-in",
        help="Ne pas mettre de pause de connexion manuelle.",
    ),
):
    cfg = load_config(config)
    downloads.mkdir(parents=True, exist_ok=True)
    profiles.mkdir(parents=True, exist_ok=True)

    if vendor is not None:
        vendor = vendor.lower().strip()
        if vendor not in VENDOR_MODULES:
            supported = ", ".join(VENDOR_MODULES)
            raise typer.BadParameter(f"Fournisseur non supporté: {vendor}. Valeurs: {supported}")
        if vendor not in cfg["invoices"]:
            raise typer.BadParameter(f"{vendor} n'existe pas dans {config}")

    results: list[CollectResult] = []

    invoice_items = cfg["invoices"].items()
    if vendor is not None:
        invoice_items = [(vendor, cfg["invoices"][vendor])]

    for vendor_name, vendor_cfg in invoice_items:
        if vendor_name not in VENDOR_MODULES:
            results.append(CollectResult.error(vendor_name, "", f"Fournisseur non supporté: {vendor_name}"))
            continue

        module = importlib.import_module(VENDOR_MODULES[vendor_name])
        months = vendor_cfg.get("months", [])

        for period in months:
            ensure_period(period)
            console.print(f"\n[bold]Collecte {vendor_name} {period}[/bold]")
            try:
                result = module.collect_invoice(
                    period=period,
                    download_root=downloads,
                    profiles_root=profiles,
                    headless=headless,
                    assume_logged_in=assume_logged_in,
                    options=vendor_cfg,
                )
            except Exception as exc:  # noqa: BLE001
                result = CollectResult.error(vendor_name, period, str(exc))
            results.append(result)
            console.print(f"Statut: [bold]{result.status}[/bold] - {result.message}")

    write_manifest(results, manifest)

    table = Table(title="Rapport de collecte")
    table.add_column("Fournisseur")
    table.add_column("Période")
    table.add_column("Statut")
    table.add_column("Fichier")
    table.add_column("Message")
    for row in results:
        table.add_row(row.vendor, row.period, row.status, row.file, row.message)
    console.print(table)
    console.print(f"\nRapport écrit dans: [bold]{manifest}[/bold]")


@app.command()
def init_profiles(
    profiles: Path = typer.Option(Path("browser_profiles"), "--profiles", "-p"),
):
    """Créer les dossiers de profils persistants pour connexion manuelle initiale."""
    for vendor_name in VENDOR_MODULES:
        (profiles / vendor_name).mkdir(parents=True, exist_ok=True)
    console.print(f"Profils créés dans: [bold]{profiles}[/bold]")


if __name__ == "__main__":
    app()
