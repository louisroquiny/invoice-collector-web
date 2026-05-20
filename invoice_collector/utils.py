import hashlib
import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^\w\-. ]+", "_", filename.strip())
    return cleaned or "invoice.pdf"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_period(period: str) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}", period):
        raise ValueError(f"Période invalide: {period}. Format attendu: YYYY-MM")
