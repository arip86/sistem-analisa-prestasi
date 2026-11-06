from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import pandas as pd

from config.constants import ALL_COLUMNS, LEVEL_ALIASES, PERINGKAT_ALIASES
from modules.data_cleaner import clean_text
from modules.date_helper import parse_date


def normalize_identity(value: Any) -> Optional[str]:
    text = clean_text(value)
    if text is None:
        return None
    text = re.sub(r"\s+", "", text)
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    if re.fullmatch(r"[+-]?\d+(\.\d+)?[eE][+-]?\d+", text):
        try:
            text = str(int(float(text)))
        except (ValueError, OverflowError):
            pass
    return text


def normalize_level(value: Any) -> Optional[str]:
    text = clean_text(value)
    if text is None:
        return None
    key = re.sub(r"[\s_-]+", " ", text).strip().upper()
    return LEVEL_ALIASES.get(key, key)


def normalize_peringkat(value: Any) -> Optional[str]:
    text = clean_text(value)
    if text is None:
        return None
    key = re.sub(r"[\s_-]+", " ", text).strip().upper()
    return PERINGKAT_ALIASES.get(key, key)


def normalize_category(value: Any) -> Optional[str]:
    text = clean_text(value)
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).upper()


def normalize_bentuk(value: Any) -> Optional[str]:
    text = clean_text(value)
    if text is None:
        return None
    lower = text.lower()
    if lower == "daring":
        return "Daring"
    if lower == "luring":
        return "Luring"
    return text


def normalize_kelompok(value: Any) -> Optional[str]:
    text = clean_text(value)
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).upper()


def normalize_url(value: Any) -> Optional[str]:
    text = clean_text(value)
    if text is None:
        return None
    text = text.strip()
    lower = text.lower()
    if lower.startswith("https://"):
        return "https://" + text[8:]
    if lower.startswith("http://"):
        return "http://" + text[7:]
    if lower.startswith("www.") or re.match(r"^[a-z0-9.-]+\.[a-z]{2,}(/|$)", lower):
        return "https://" + text
    return text


def is_valid_url(value: Optional[str]) -> bool:
    if not value:
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def normalize_number(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = clean_text(value)
    if text is None:
        return None
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", text):
        text = text.replace(".", "")
    text = text.replace(",", ".")
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return int(number)


def normalize_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in ALL_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = None
    normalized["level"] = normalized["level"].map(normalize_level)
    normalized["kategori"] = normalized["kategori"].map(normalize_category)
    normalized["lomba"] = normalized["lomba"].map(clean_text)
    normalized["cabang"] = normalized["cabang"].map(clean_text)
    normalized["penyelenggara"] = normalized["penyelenggara"].map(clean_text)
    normalized["peringkat"] = normalized["peringkat"].map(normalize_peringkat)
    normalized["jumlah_unit_peserta"] = normalized["jumlah_unit_peserta"].map(normalize_number)
    normalized["kelompok_prestasi"] = normalized["kelompok_prestasi"].map(normalize_kelompok)
    normalized["bentuk"] = normalized["bentuk"].map(normalize_bentuk)
    normalized["url_peserta"] = normalized["url_peserta"].map(normalize_url)
    normalized["url_sertifikat"] = normalized["url_sertifikat"].map(normalize_url)
    normalized["tgl_sertifikat"] = normalized["tgl_sertifikat"].map(parse_date)
    normalized["url_foto_upp"] = normalized["url_foto_upp"].map(normalize_url)
    normalized["url_dokumen_undangan"] = normalized["url_dokumen_undangan"].map(normalize_url)
    normalized["keterangan"] = normalized["keterangan"].map(clean_text)
    normalized["mahasiswa_nim"] = normalized["mahasiswa_nim"].map(normalize_identity)
    normalized["mahasiswa_nama"] = normalized["mahasiswa_nama"].map(clean_text)
    normalized["dosen_nuptk"] = normalized["dosen_nuptk"].map(normalize_identity)
    normalized["dosen_nama"] = normalized["dosen_nama"].map(clean_text)
    normalized["dosen_url_surat_tugas"] = normalized["dosen_url_surat_tugas"].map(normalize_url)
    if "source_row_number" not in normalized.columns:
        normalized["source_row_number"] = range(2, len(normalized) + 2)
    return normalized


def _parts_text(parts: List[Any]) -> str:
    cleaned = ["" if part is None else str(part).strip() for part in parts]
    return "|".join(cleaned)


def _date_text(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return "" if value is None else str(value)


def build_fingerprint(row: Dict[str, Any]) -> str:
    text = _parts_text(
        [
            row.get("level"),
            row.get("kategori"),
            row.get("lomba"),
            row.get("cabang"),
            row.get("penyelenggara"),
            row.get("peringkat"),
            _date_text(row.get("tgl_sertifikat")),
            row.get("mahasiswa_nim"),
            row.get("dosen_nuptk"),
            row.get("url_sertifikat"),
        ]
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_duplicate_group_key(row: Dict[str, Any]) -> str:
    text = _parts_text(
        [
            row.get("level"),
            row.get("kategori"),
            row.get("lomba"),
            row.get("cabang"),
            row.get("penyelenggara"),
            row.get("peringkat"),
            _date_text(row.get("tgl_sertifikat")),
            row.get("mahasiswa_nim"),
        ]
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
