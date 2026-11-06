from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from config.constants import NIM_PATTERN, NUPTK_PATTERN
from modules.analysis.common import join_unique, split_multi

FIELD_LABELS = {
    "level": "Level",
    "kategori_kode": "Kategori",
    "lomba": "Nama lomba",
    "cabang": "Cabang lomba",
    "penyelenggara": "Penyelenggara",
    "peringkat": "Peringkat",
    "tgl_sertifikat": "Tanggal sertifikat",
    "mahasiswa_nim": "NIM mahasiswa",
    "mahasiswa_nama": "Nama mahasiswa",
    "dosen_nuptk": "ID dosen",
    "dosen_nama": "Nama dosen",
    "jumlah_unit_peserta": "Jumlah unit peserta",
    "kelompok_prestasi": "Kelompok prestasi",
    "bentuk": "Bentuk prestasi",
    "url_peserta": "URL peserta",
    "url_sertifikat": "URL sertifikat",
    "url_foto_upp": "URL foto UPP",
    "url_dokumen_undangan": "URL dokumen undangan",
    "keterangan": "Keterangan",
    "dosen_url_surat_tugas": "URL surat tugas dosen",
}

CORE_FIELDS = [
    "level",
    "kategori_kode",
    "lomba",
    "cabang",
    "penyelenggara",
    "peringkat",
    "tgl_sertifikat",
    "mahasiswa_nim",
    "mahasiswa_nama",
    "dosen_nuptk",
    "dosen_nama",
]

OPTIONAL_FIELDS = [
    "jumlah_unit_peserta",
    "kelompok_prestasi",
    "bentuk",
    "url_peserta",
    "url_sertifikat",
    "url_foto_upp",
    "url_dokumen_undangan",
    "keterangan",
    "dosen_url_surat_tugas",
]

DOCUMENT_FIELDS = [
    "url_sertifikat",
    "url_peserta",
    "url_foto_upp",
    "url_dokumen_undangan",
    "dosen_url_surat_tugas",
]

COMPLETENESS_COLUMNS = ["field", "label", "kelompok", "terisi", "kosong", "persentase"]
IDENTITY_COLUMNS = ["field", "label", "terisi", "kosong", "tidak_valid", "persentase_valid"]
DUPLICATE_COLUMNS = [
    "prestasi_id",
    "jumlah_baris",
    "nim",
    "mahasiswa",
    "lomba",
    "peringkat",
    "tanggal",
    "dosen",
    "jumlah_sertifikat",
]
INCOMPLETE_COLUMNS = [
    "prestasi_id",
    "mahasiswa_nama",
    "lomba",
    "tahun",
    "field_kosong",
    "jumlah_field_kosong",
]


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and not value.strip()


def _missing_mask(series: pd.Series) -> pd.Series:
    return series.map(is_missing)


def _field_group(field: str) -> str:
    if field in CORE_FIELDS:
        return "Wajib"
    if field in DOCUMENT_FIELDS:
        return "Dokumen"
    return "Opsional"


def field_completeness(
    frame: pd.DataFrame,
    fields: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    if frame.empty:
        return _empty(COMPLETENESS_COLUMNS)
    selected = list(fields) if fields is not None else CORE_FIELDS + OPTIONAL_FIELDS
    rows = []
    total = len(frame)
    for field in selected:
        if field not in frame.columns:
            continue
        missing = int(_missing_mask(frame[field]).sum())
        filled = total - missing
        rows.append(
            {
                "field": field,
                "label": FIELD_LABELS.get(field, field),
                "kelompok": _field_group(field),
                "terisi": filled,
                "kosong": missing,
                "persentase": (filled / total * 100) if total else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=COMPLETENESS_COLUMNS)


def identity_validation(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(IDENTITY_COLUMNS)
    checks = [
        ("mahasiswa_nim", "NIM mahasiswa", NIM_PATTERN),
        ("dosen_nuptk", "NUPTK dosen", NUPTK_PATTERN),
    ]
    rows = []
    total = len(frame)
    for field, label, pattern in checks:
        if field not in frame.columns:
            continue
        missing_mask = _missing_mask(frame[field])
        invalid = 0
        for value in frame.loc[~missing_mask, field].tolist():
            tokens = split_multi(value)
            if not tokens or any(not re.fullmatch(pattern, token) for token in tokens):
                invalid += 1
        filled = int((~missing_mask).sum())
        valid = filled - invalid
        rows.append(
            {
                "field": field,
                "label": label,
                "terisi": filled,
                "kosong": int(missing_mask.sum()),
                "tidak_valid": invalid,
                "persentase_valid": (valid / total * 100) if total else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=IDENTITY_COLUMNS)


def certificate_completeness(frame: pd.DataFrame) -> pd.DataFrame:
    return field_completeness(frame, DOCUMENT_FIELDS)


def duplicate_groups(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "is_duplicate_suspect" not in frame.columns:
        return _empty(DUPLICATE_COLUMNS)
    data = frame[frame["is_duplicate_suspect"] == True].copy()  # noqa: E712
    if data.empty:
        return _empty(DUPLICATE_COLUMNS)
    data["duplicate_group_key"] = data["duplicate_group_key"].fillna("Tanpa grup")
    data["tanggal_label"] = pd.to_datetime(
        data["tgl_sertifikat"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    rows = []
    for group_key, group in data.groupby("duplicate_group_key", dropna=False):
        rows.append(
            {
                "prestasi_id": join_unique(group["prestasi_id"].astype(str)),
                "jumlah_baris": int(group["prestasi_id"].nunique()),
                "nim": join_unique(group["mahasiswa_nim"]),
                "mahasiswa": join_unique(group["mahasiswa_nama"]),
                "lomba": join_unique(group["lomba"]),
                "peringkat": join_unique(group["peringkat_label"]),
                "tanggal": join_unique(group["tanggal_label"]),
                "dosen": join_unique(group["dosen_nama"]),
                "jumlah_sertifikat": int(group["url_sertifikat"].nunique(dropna=True))
                if "url_sertifikat" in group
                else 0,
                "_group": group_key,
            }
        )
    result = pd.DataFrame(rows)
    return (
        result.sort_values(["jumlah_baris", "lomba"], ascending=[False, True])
        .drop(columns=["_group"])
        .reset_index(drop=True)[DUPLICATE_COLUMNS]
    )


def incomplete_records(
    frame: pd.DataFrame,
    fields: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    if frame.empty:
        return _empty(INCOMPLETE_COLUMNS)
    selected = [
        field
        for field in (list(fields) if fields is not None else OPTIONAL_FIELDS)
        if field in frame.columns
    ]
    if not selected:
        return _empty(INCOMPLETE_COLUMNS)
    missing = frame[selected].apply(_missing_mask)
    counts = missing.sum(axis=1)
    data = frame[counts > 0].copy()
    if data.empty:
        return _empty(INCOMPLETE_COLUMNS)
    data["field_kosong"] = missing.loc[counts > 0].apply(
        lambda row: ", ".join(
            FIELD_LABELS.get(field, field) for field, value in row.items() if value
        ),
        axis=1,
    )
    data["jumlah_field_kosong"] = counts.loc[counts > 0].astype(int)
    data["tahun"] = data["tahun"].fillna("-").astype(str)
    return (
        data.sort_values(
            ["jumlah_field_kosong", "tahun", "lomba"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)[INCOMPLETE_COLUMNS]
    )


def quality_metrics(frame: pd.DataFrame) -> Dict[str, Any]:
    if frame.empty:
        return {
            "total_prestasi": 0,
            "field_lengkap": 0,
            "rata_kelengkapan": 0.0,
            "duplikat_baris": 0,
            "duplikat_grup": 0,
            "duplikat_ekstra": 0,
            "data_tidak_lengkap": 0,
            "nim_tidak_valid": 0,
            "nuptk_tidak_valid": 0,
        }
    completeness = field_completeness(frame)
    duplicates = duplicate_groups(frame)
    incomplete = incomplete_records(frame)
    identities = identity_validation(frame)
    nim_invalid = identities.loc[identities["field"] == "mahasiswa_nim", "tidak_valid"]
    nuptk_invalid = identities.loc[identities["field"] == "dosen_nuptk", "tidak_valid"]
    return {
        "total_prestasi": int(len(frame)),
        "field_lengkap": int((completeness["persentase"] == 100).sum())
        if not completeness.empty
        else 0,
        "rata_kelengkapan": float(completeness["persentase"].mean())
        if not completeness.empty
        else 0.0,
        "duplikat_baris": int((frame["is_duplicate_suspect"] == True).sum())  # noqa: E712
        if "is_duplicate_suspect" in frame
        else 0,
        "duplikat_grup": int(len(duplicates)),
        "duplikat_ekstra": int(
            max(0, duplicates["jumlah_baris"].sum() - len(duplicates))
        )
        if not duplicates.empty
        else 0,
        "data_tidak_lengkap": int(len(incomplete)),
        "nim_tidak_valid": int(nim_invalid.iloc[0]) if not nim_invalid.empty else 0,
        "nuptk_tidak_valid": int(nuptk_invalid.iloc[0]) if not nuptk_invalid.empty else 0,
    }


def completeness_summary(frame: pd.DataFrame) -> pd.DataFrame:
    data = field_completeness(frame)
    if data.empty:
        return data
    return data.sort_values(["persentase", "field"], ascending=[True, True]).reset_index(
        drop=True
    )


def document_gap_records(frame: pd.DataFrame) -> pd.DataFrame:
    return incomplete_records(frame, DOCUMENT_FIELDS)
