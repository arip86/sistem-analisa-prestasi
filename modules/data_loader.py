from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from config.constants import COLUMN_ALIASES, REQUIRED_COLUMNS


class DataLoadError(Exception):
    pass


@dataclass
class LoadedSource:
    frame: pd.DataFrame
    source_name: str
    sheet_name: Optional[str]
    header_row_index: int
    source_type: str
    detected_columns: List[str] = field(default_factory=list)
    missing_columns: List[str] = field(default_factory=list)


def normalize_header(value) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _alias_lookup() -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        lookup[normalize_header(canonical)] = canonical
        for alias in aliases:
            lookup[normalize_header(alias)] = canonical
    return lookup


ALIAS_LOOKUP = _alias_lookup()


def detect_header_row(raw: pd.DataFrame, max_scan: int = 20) -> Tuple[Optional[int], List[str], List[str]]:
    best_index: Optional[int] = None
    best_columns: List[str] = []
    best_missing = list(REQUIRED_COLUMNS)
    for index in range(min(max_scan, len(raw))):
        row = raw.iloc[index].tolist()
        mapped = [ALIAS_LOOKUP.get(normalize_header(cell)) for cell in row]
        columns = [column for column in mapped if column]
        unique_columns = list(dict.fromkeys(columns))
        missing = [column for column in REQUIRED_COLUMNS if column not in unique_columns]
        score = len(REQUIRED_COLUMNS) - len(missing)
        if score > len(REQUIRED_COLUMNS) - len(best_missing):
            best_index = index
            best_columns = unique_columns
            best_missing = missing
        if not missing:
            return index, unique_columns, []
    if best_index is not None and len(best_missing) < len(REQUIRED_COLUMNS):
        return best_index, best_columns, best_missing
    return None, [], list(REQUIRED_COLUMNS)


def build_dataframe(raw: pd.DataFrame, header_index: int) -> pd.DataFrame:
    header_cells = raw.iloc[header_index].tolist()
    canonical_headers: List[str] = []
    seen: set[str] = set()
    for cell in header_cells:
        canonical = ALIAS_LOOKUP.get(normalize_header(cell))
        if canonical and canonical not in seen:
            canonical_headers.append(canonical)
            seen.add(canonical)
        else:
            canonical_headers.append(f"_extra_{len(canonical_headers)}")
    data = raw.iloc[header_index + 1 :].copy()
    data.columns = canonical_headers
    data["source_row_number"] = data.index + header_index + 2
    data = data.loc[:, [column for column in data.columns if not str(column).startswith("_extra_")]]
    data = data.dropna(how="all")
    if not data.empty:
        non_empty = data.apply(
            lambda row: any(
                str(value).strip() not in ("", "nan", "None") for value in row if value is not None
            ),
            axis=1,
        )
        data = data.loc[non_empty]
    return data.reset_index(drop=True)


def _read_excel(content: bytes) -> LoadedSource:
    workbook = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    best_candidate: Optional[LoadedSource] = None
    for sheet_name in workbook.sheet_names:
        raw = pd.read_excel(workbook, sheet_name=sheet_name, header=None, dtype=object)
        if raw.empty:
            continue
        header_index, detected, missing = detect_header_row(raw)
        if header_index is None:
            continue
        candidate = LoadedSource(
            frame=build_dataframe(raw, header_index),
            source_name="",
            sheet_name=sheet_name,
            header_row_index=header_index,
            source_type="excel",
            detected_columns=detected,
            missing_columns=missing,
        )
        if not missing:
            return candidate
        if best_candidate is None or len(missing) < len(best_candidate.missing_columns):
            best_candidate = candidate
    if best_candidate is None:
        raise DataLoadError("Tidak menemukan sheet dengan struktur kolom prestasi yang dikenali.")
    return best_candidate


def _detect_csv_separator(content: bytes) -> str:
    sample = content[:8192].decode("utf-8-sig", errors="replace")
    lines = sample.splitlines()[:5]
    candidates = [",", ";", "\t", "|"]
    scores = {separator: sum(line.count(separator) for line in lines) for separator in candidates}
    return max(scores, key=scores.get)


def _read_csv(content: bytes) -> LoadedSource:
    separator = _detect_csv_separator(content)
    last_error: Optional[Exception] = None
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            raw = pd.read_csv(
                io.BytesIO(content),
                header=None,
                dtype=object,
                sep=separator,
                keep_default_na=False,
                encoding=encoding,
            )
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise DataLoadError("File CSV tidak dapat dibaca.") from last_error
    if raw.empty:
        raise DataLoadError("File CSV kosong.")
    header_index, detected, missing = detect_header_row(raw)
    if header_index is None:
        raise DataLoadError("Header kolom wajib tidak ditemukan pada file CSV.")
    return LoadedSource(
        frame=build_dataframe(raw, header_index),
        source_name="",
        sheet_name=None,
        header_row_index=header_index,
        source_type="csv",
        detected_columns=detected,
        missing_columns=missing,
    )


def load_source(content: bytes, filename: str) -> LoadedSource:
    suffix = Path(filename).suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        loaded = _read_excel(content)
    elif suffix == ".csv":
        loaded = _read_csv(content)
    elif suffix == ".xls":
        raise DataLoadError("Format .xls lama belum didukung. Simpan file sebagai .xlsx atau .csv.")
    else:
        raise DataLoadError("Format file tidak didukung. Gunakan .xlsx atau .csv.")
    loaded.source_name = filename
    if loaded.missing_columns:
        missing = ", ".join(loaded.missing_columns)
        raise DataLoadError(f"Kolom wajib tidak ditemukan: {missing}.")
    return loaded


def load_source_path(path: str | Path) -> LoadedSource:
    file_path = Path(path)
    return load_source(file_path.read_bytes(), file_path.name)
