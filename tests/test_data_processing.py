from __future__ import annotations

from datetime import date

from config import settings
from modules.data_cleaner import clean_text
from modules.data_loader import load_source, load_source_path
from modules.data_normalizer import (
    build_duplicate_group_key,
    build_fingerprint,
    normalize_category,
    normalize_dataframe,
    normalize_level,
    normalize_number,
    normalize_peringkat,
    normalize_url,
)
from modules.data_validator import validate_dataframe, validate_row
from modules.date_helper import format_date_id, parse_date


def _source_frame():
    loaded = load_source_path(settings.EXCEL_SOURCE_FILE)
    return loaded, normalize_dataframe(loaded.frame)


def test_clean_text_collapses_whitespace():
    assert clean_text("  Lomba   Nasional \u00a0 2025 ") == "Lomba Nasional 2025"
    assert clean_text(None) is None
    assert clean_text("nan") is None


def test_date_helpers():
    assert parse_date("2025-12-31") == date(2025, 12, 31)
    assert parse_date("31/12/2025") == date(2025, 12, 31)
    assert parse_date("31-12-2025") == date(2025, 12, 31)
    assert format_date_id(date(2025, 1, 2)) == "02-01-2025"


def test_normalizers():
    assert normalize_level("Nasional") == "NAS"
    assert normalize_level("Internasional") == "INT"
    assert normalize_peringkat("Juara II") == "JUARA2"
    assert normalize_peringkat("Juara 1") == "JUARA1"
    assert normalize_category(" risnovssh ") == "RISNOVSSH"
    assert normalize_number("1.000") == 1000
    assert normalize_url("app.puskanas.id") == "https://app.puskanas.id"
    assert normalize_url("https://example.com") == "https://example.com"


def test_fingerprint_is_stable_and_sensitive():
    row = {
        "level": "NAS",
        "kategori": "RISNOV",
        "lomba": "Lomba A",
        "cabang": "Cabang A",
        "penyelenggara": "Penyelenggara A",
        "peringkat": "JUARA1",
        "tgl_sertifikat": date(2025, 1, 1),
        "mahasiswa_nim": "0110124001",
        "dosen_nuptk": "1234567890123456",
        "url_sertifikat": "https://example.com/sertifikat",
    }
    same = dict(row)
    changed = dict(row)
    changed["peringkat"] = "JUARA2"
    changed_attachment = dict(row)
    changed_attachment["dosen_nuptk"] = "9999999999999999"
    changed_attachment["url_sertifikat"] = "https://example.com/lain"
    assert build_fingerprint(row) == build_fingerprint(same)
    assert build_fingerprint(row) != build_fingerprint(changed)
    assert build_duplicate_group_key(row) == build_duplicate_group_key(changed_attachment)
    assert build_duplicate_group_key(row) != build_duplicate_group_key(changed)


def test_real_source_loads_and_validates():
    loaded, normalized = _source_frame()
    assert loaded.sheet_name == "Template Prestasi Baru"
    assert len(normalized) == 292
    result = validate_dataframe(normalized)
    assert result.total_rows == 292
    assert result.valid_rows == 292
    assert result.invalid_rows == 0
    assert result.duplicate_suspects == 8
    assert result.file_duplicates == 0


def test_csv_source_loads():
    content = (
        "level,kategori,lomba,cabang,penyelenggara,peringkat,tgl_sertifikat,"
        "mahasiswa_nim,mahasiswa_nama,dosen_nuptk,dosen_nama\n"
        "Nasional,RISNOV,Lomba A,Cabang A,Penyelenggara A,Juara 1,2025-01-10,"
        "0110124001,Ani,1234567890123456,Dosen A\n"
    ).encode("utf-8")
    loaded = load_source(content, "data.csv")
    normalized = normalize_dataframe(loaded.frame)
    assert loaded.source_type == "csv"
    assert len(normalized) == 1
    assert normalized.iloc[0]["level"] == "NAS"
    assert normalized.iloc[0]["peringkat"] == "JUARA1"


def test_validate_row_detects_invalid_values():
    _, normalized = _source_frame()
    row = normalized.iloc[0].to_dict()
    row["mahasiswa_nim"] = "ABC"
    row["dosen_nuptk"] = "123"
    row["level"] = "UNKNOWN"
    row["peringkat"] = "UNKNOWN"
    row["url_sertifikat"] = "bukan-url"
    errors = validate_row(row)
    assert any("NIM" in error for error in errors)
    assert any("NUPTK" in error for error in errors)
    assert any("Level" in error for error in errors)
    assert any("Peringkat" in error for error in errors)
    assert any("URL" in error for error in errors)
