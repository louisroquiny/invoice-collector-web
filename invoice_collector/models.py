from dataclasses import dataclass
from pathlib import Path


@dataclass
class CollectResult:
    vendor: str
    period: str
    status: str
    file: str = ""
    message: str = ""

    @classmethod
    def found(cls, vendor: str, period: str, path: Path, message: str = "Facture téléchargée"):
        return cls(vendor=vendor, period=period, status="found", file=str(path), message=message)

    @classmethod
    def missing(cls, vendor: str, period: str, message: str):
        return cls(vendor=vendor, period=period, status="missing", message=message)

    @classmethod
    def error(cls, vendor: str, period: str, message: str):
        return cls(vendor=vendor, period=period, status="error", message=message)
