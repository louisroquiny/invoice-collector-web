import csv
from datetime import datetime
from pathlib import Path

from invoice_collector.models import CollectResult
from invoice_collector.utils import sha256_file


FIELDNAMES = [
    "vendor",
    "period",
    "status",
    "file",
    "sha256",
    "message",
    "collected_at",
]


def write_manifest(rows: list[CollectResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            file_hash = ""
            if row.file and Path(row.file).exists():
                file_hash = sha256_file(Path(row.file))
            writer.writerow(
                {
                    "vendor": row.vendor,
                    "period": row.period,
                    "status": row.status,
                    "file": row.file,
                    "sha256": file_hash,
                    "message": row.message,
                    "collected_at": now,
                }
            )
