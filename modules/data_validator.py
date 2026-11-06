from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import pandas as pd

from config.constants import (
    ALLOWED_LEVELS,
    ALLOWED_PERINGKAT,
    NIM_PATTERN,
    NUPTK_PATTERN,
    REQUIRED_COLUMNS,
    URL_COLUMNS,
)
from modules.data_normalizer import (
    build_duplicate_group_key,
    build_fingerprint,
    is_valid_url,
)


@dataclass
class ValidationResult:
    valid: pd.DataFrame
    invalid: pd.DataFrame
    duplicates: pd.DataFrame
    all_rows: pd.DataFrame
    total_rows: int
    warnings: List[str] = field(default_factory=list)
    duplicate_suspects: int = 0
    file_duplicates: int = 0
    existing_duplicates: int = 0

    @property
    def valid_rows(self) -> int:
        return len(self.valid)

    @property
    def invalid_rows(self) -> int:
        return len(self.invalid)

    @property
    def duplicate_rows(self) -> int:
        return len(self.duplicates)

    @property
    def ready_rows(self) -> int:
        return len(self.valid)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and not value.strip()


def validate_row(row: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for column in REQUIRED_COLUMNS:
        if _is_empty(row.get(column)):
            errors.append(f"Kolom {column} wajib diisi.")

    nim = row.get("mahasiswa_nim")
    if not _is_empty(nim) and not re.fullmatch(NIM_PATTERN, str(nim)):
        errors.append("NIM harus berupa angka 5-20 digit.")

    nuptk = row.get("dosen_nuptk")
    if not _is_empty(nuptk) and not re.fullmatch(NUPTK_PATTERN, str(nuptk)):
        errors.append("NUPTK harus berupa angka 16 digit.")

    level = row.get("level")
    if not _is_empty(level) and level not in ALLOWED_LEVELS:
        errors.append(f"Level kompetisi tidak dikenali: {level}.")

    peringkat = row.get("peringkat")
    if not _is_empty(peringkat) and peringkat not in ALLOWED_PERINGKAT:
        errors.append(f"Peringkat tidak dikenali: {peringkat}.")

    if _is_empty(row.get("tgl_sertifikat")):
        errors.append("Tanggal sertifikat tidak valid.")

    jumlah = row.get("jumlah_unit_peserta")
    if not _is_empty(jumlah):
        try:
            if int(jumlah) <= 0:
                errors.append("Jumlah unit peserta harus lebih dari 0.")
        except (TypeError, ValueError):
            errors.append("Jumlah unit peserta harus berupa angka.")

    for column in URL_COLUMNS:
        value = row.get(column)
        if not _is_empty(value) and not is_valid_url(str(value)):
            errors.append(f"Format URL {column} tidak valid.")
    return errors


def validate_dataframe(
    frame: pd.DataFrame,
    existing_fingerprints: Optional[Set[str]] = None,
) -> ValidationResult:
    validated = frame.copy()
    errors_list: List[List[str]] = [validate_row(row.to_dict()) for _, row in validated.iterrows()]
    validated["validation_errors"] = errors_list
    validated["validation_warnings"] = [[] for _ in range(len(validated))]
    validated["fingerprint"] = validated.apply(lambda row: build_fingerprint(row.to_dict()), axis=1)
    validated["duplicate_group_key"] = validated.apply(
        lambda row: build_duplicate_group_key(row.to_dict()), axis=1
    )

    seen: Dict[str, int] = {}
    in_file_duplicate = [False] * len(validated)
    for position, (index, row) in enumerate(validated.iterrows()):
        fingerprint = row["fingerprint"]
        source_row = row.get("source_row_number")
        if fingerprint in seen:
            in_file_duplicate[position] = True
            validated.at[index, "validation_errors"] = list(
                validated.at[index, "validation_errors"]
            ) + [f"Duplikat dalam file dengan baris {seen[fingerprint]}."]
        else:
            seen[fingerprint] = int(source_row) if not pd.isna(source_row) else int(index) + 2
    validated["is_duplicate_file"] = in_file_duplicate

    existing = existing_fingerprints or set()
    validated["is_duplicate_db"] = validated["fingerprint"].isin(existing)

    group_counts = validated.groupby("duplicate_group_key")["fingerprint"].nunique()
    suspect_groups = set(group_counts[group_counts > 1].index.tolist())
    validated["is_duplicate_suspect"] = validated["duplicate_group_key"].isin(suspect_groups)
    for index, row in validated.iterrows():
        if row["is_duplicate_suspect"]:
            validated.at[index, "validation_warnings"] = list(
                validated.at[index, "validation_warnings"]
            ) + [
                "Duplikat potensial: event dan mahasiswa sama dengan baris lain, "
                "tetapi dosen atau URL sertifikat berbeda."
            ]

    invalid_mask = validated["validation_errors"].map(len) > 0
    db_duplicate_mask = ~invalid_mask & validated["is_duplicate_db"]
    valid_mask = ~invalid_mask & ~validated["is_duplicate_db"]

    valid = validated.loc[valid_mask].copy().reset_index(drop=True)
    invalid = validated.loc[invalid_mask].copy().reset_index(drop=True)
    duplicates = validated.loc[db_duplicate_mask].copy().reset_index(drop=True)

    warnings: List[str] = []
    file_duplicates = int(validated["is_duplicate_file"].sum())
    existing_duplicates = int(validated["is_duplicate_db"].sum())
    if file_duplicates:
        warnings.append(f"Ditemukan {file_duplicates} duplikat di dalam file.")
    if existing_duplicates:
        warnings.append(f"Ditemukan {existing_duplicates} baris yang sudah ada di database.")
    if suspect_groups:
        warnings.append(
            f"Ditemukan {int(validated['is_duplicate_suspect'].sum())} baris sebagai duplikat potensial."
        )

    return ValidationResult(
        valid=valid,
        invalid=invalid,
        duplicates=duplicates,
        all_rows=validated,
        total_rows=len(validated),
        warnings=warnings,
        duplicate_suspects=int(validated["is_duplicate_suspect"].sum()),
        file_duplicates=file_duplicates,
        existing_duplicates=existing_duplicates,
    )
