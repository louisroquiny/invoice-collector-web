from pathlib import Path

import pytest

from invoice_collector.utils import ensure_period, sanitize_filename, unique_path


def test_sanitize_filename_removes_bad_chars():
    assert sanitize_filename("facture:mai/2026?.pdf") == "facture_mai_2026_.pdf"


def test_ensure_period_accepts_valid_period():
    ensure_period("2026-05")


def test_ensure_period_rejects_invalid_period():
    with pytest.raises(ValueError):
        ensure_period("05/2026")


def test_unique_path(tmp_path: Path):
    original = tmp_path / "invoice.pdf"
    original.write_text("existing", encoding="utf-8")
    assert unique_path(original).name == "invoice_1.pdf"
