from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd

from config.constants import (
    CATEGORY_LABELS,
    CATEGORY_SHORT_LABELS,
    LEVEL_LABELS,
    LEVEL_POINTS,
    PERINGKAT_LABELS,
    RANK_POINTS,
)

STUDENT_RANK_COLUMNS = [
    "ranking",
    "nim",
    "nama",
    "jumlah_prestasi",
    "juara1",
    "juara2",
    "juara3",
    "poin",
]
DOSEN_RANK_COLUMNS = [
    "ranking",
    "nuptk",
    "nama",
    "jumlah_prestasi",
    "jumlah_mahasiswa",
    "juara1",
    "juara2",
    "juara3",
    "poin",
]


def _empty(columns: List[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def add_points(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["level_points"] = data["level"].map(LEVEL_POINTS).fillna(1).astype(int)
    data["rank_points"] = data["peringkat"].map(RANK_POINTS).fillna(1).astype(int)
    data["poin"] = data["level_points"] * data["rank_points"]
    return data


def filter_data(
    frame: pd.DataFrame,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    kategori: Optional[List[str]] = None,
    level: Optional[List[str]] = None,
    peringkat: Optional[List[str]] = None,
    tahun: Optional[List[int]] = None,
) -> pd.DataFrame:
    data = frame.copy()
    if data.empty:
        return data
    if start_date is not None:
        data = data[data["tgl_sertifikat"].dt.date >= start_date]
    if end_date is not None:
        data = data[data["tgl_sertifikat"].dt.date <= end_date]
    if kategori:
        data = data[data["kategori_kode"].isin(kategori)]
    if level:
        data = data[data["level"].isin(level)]
    if peringkat:
        data = data[data["peringkat"].isin(peringkat)]
    if tahun:
        data = data[data["tahun"].isin(tahun)]
    return data.reset_index(drop=True)


def _split_multi(value: Any) -> List[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def explode_students(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=["prestasi_id", "nim", "nama", "level", "peringkat", "poin", "tahun"]
        )
    data = add_points(frame)
    records: List[Dict[str, Any]] = []
    for row in data.to_dict("records"):
        nims = _split_multi(row.get("mahasiswa_nim"))
        names = _split_multi(row.get("mahasiswa_nama"))
        for index, nim in enumerate(nims):
            records.append(
                {
                    "prestasi_id": row.get("prestasi_id"),
                    "nim": nim,
                    "nama": names[index] if index < len(names) else (names[0] if names else ""),
                    "level": row.get("level"),
                    "peringkat": row.get("peringkat"),
                    "poin": row.get("poin", 0),
                    "tahun": row.get("tahun"),
                }
            )
    return pd.DataFrame(records)


def explode_dosen(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=["prestasi_id", "nuptk", "nama", "nim", "level", "peringkat", "poin", "tahun"]
        )
    data = add_points(frame)
    records: List[Dict[str, Any]] = []
    for row in data.to_dict("records"):
        nuptks = _split_multi(row.get("dosen_nuptk"))
        names = _split_multi(row.get("dosen_nama"))
        nims = _split_multi(row.get("mahasiswa_nim"))
        for index, nuptk in enumerate(nuptks):
            records.append(
                {
                    "prestasi_id": row.get("prestasi_id"),
                    "nuptk": nuptk,
                    "nama": names[index] if index < len(names) else (names[0] if names else ""),
                    "nim": "; ".join(nims),
                    "level": row.get("level"),
                    "peringkat": row.get("peringkat"),
                    "poin": row.get("poin", 0),
                    "tahun": row.get("tahun"),
                }
            )
    return pd.DataFrame(records)


def summary_metrics(frame: pd.DataFrame) -> Dict[str, Any]:
    if frame.empty:
        return {
            "total_prestasi": 0,
            "total_mahasiswa": 0,
            "total_dosen": 0,
            "total_kompetisi": 0,
            "nasional": 0,
            "internasional": 0,
            "provinsi": 0,
            "kab_kota": 0,
            "juara1": 0,
            "juara2": 0,
            "juara3": 0,
            "potensi_duplikat": 0,
            "kategori": {},
            "tahun": {},
        }
    student_nims: set[str] = set()
    for value in frame["mahasiswa_nim"]:
        student_nims.update(_split_multi(value))
    dosen_nuptks: set[str] = set()
    for value in frame["dosen_nuptk"]:
        dosen_nuptks.update(_split_multi(value))
    competition_frame = frame[["lomba", "tahun"]].copy()
    competition_frame["tahun"] = competition_frame["tahun"].fillna("-")
    total_kompetisi = competition_frame.drop_duplicates().shape[0]
    kategori_counts = (
        frame["kategori_kode"].fillna("-").value_counts().sort_index().to_dict()
    )
    tahun_counts = frame["tahun"].dropna().astype(int).value_counts().sort_index().to_dict()
    return {
        "total_prestasi": int(len(frame)),
        "total_mahasiswa": len(student_nims),
        "total_dosen": len(dosen_nuptks),
        "total_kompetisi": int(total_kompetisi),
        "nasional": int((frame["level"] == "NAS").sum()),
        "internasional": int((frame["level"] == "INT").sum()),
        "provinsi": int((frame["level"] == "PROV").sum()),
        "kab_kota": int(frame["level"].isin(["KAB", "KOTA"]).sum()),
        "juara1": int((frame["peringkat"] == "JUARA1").sum()),
        "juara2": int((frame["peringkat"] == "JUARA2").sum()),
        "juara3": int((frame["peringkat"] == "JUARA3").sum()),
        "potensi_duplikat": int(frame["is_duplicate_suspect"].sum()),
        "kategori": kategori_counts,
        "tahun": tahun_counts,
    }


def category_counts(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["kategori_kode", "kategori", "jumlah"]
    if frame.empty:
        return _empty(columns)
    data = frame.copy()
    data["kategori"] = data.apply(
        lambda row: f"{CATEGORY_SHORT_LABELS.get(row['kategori_kode'], row.get('kategori_nama') or row['kategori_kode'])} ({row['kategori_kode']})",
        axis=1,
    )
    result = data.groupby(["kategori_kode", "kategori"], as_index=False).size()
    result = result.rename(columns={"size": "jumlah"}).sort_values("jumlah", ascending=False)
    return result.reset_index(drop=True)


def level_counts(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["level", "level_label", "jumlah"]
    if frame.empty:
        return _empty(columns)
    data = frame.copy()
    data["level_label"] = data["level"].map(LEVEL_LABELS).fillna(data["level"])
    order = ["INT", "NAS", "PROV", "KAB", "KOTA"]
    result = data.groupby(["level", "level_label"], as_index=False).size()
    result = result.rename(columns={"size": "jumlah"})
    result["order"] = result["level"].map({value: index for index, value in enumerate(order)}).fillna(99)
    return result.sort_values(["order", "jumlah"], ascending=[True, False]).drop(columns=["order"]).reset_index(drop=True)


def peringkat_counts(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["peringkat", "peringkat_label", "jumlah"]
    if frame.empty:
        return _empty(columns)
    data = frame.copy()
    data["peringkat_label"] = data["peringkat"].map(PERINGKAT_LABELS).fillna(data["peringkat"])
    order = ["JUARA1", "JUARA2", "JUARA3", "HARAPAN1", "HARAPAN2", "HARAPAN3"]
    result = data.groupby(["peringkat", "peringkat_label"], as_index=False).size()
    result = result.rename(columns={"size": "jumlah"})
    result["order"] = result["peringkat"].map({value: index for index, value in enumerate(order)}).fillna(99)
    return result.sort_values(["order", "jumlah"], ascending=[True, False]).drop(columns=["order"]).reset_index(drop=True)


def year_counts(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["tahun", "jumlah"]
    if frame.empty:
        return _empty(columns)
    data = frame.dropna(subset=["tahun"])
    result = data.groupby("tahun", as_index=False).size()
    result = result.rename(columns={"size": "jumlah"})
    result["tahun"] = result["tahun"].astype(int)
    return result.sort_values("tahun").reset_index(drop=True)


def student_ranking(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(STUDENT_RANK_COLUMNS)
    data = explode_students(frame)
    if data.empty:
        return _empty(STUDENT_RANK_COLUMNS)
    grouped = (
        data.groupby(["nim", "nama"], as_index=False)
        .agg(
            jumlah_prestasi=("prestasi_id", "nunique"),
            juara1=("peringkat", lambda values: int((values == "JUARA1").sum())),
            juara2=("peringkat", lambda values: int((values == "JUARA2").sum())),
            juara3=("peringkat", lambda values: int((values == "JUARA3").sum())),
            poin=("poin", "sum"),
        )
        .sort_values(["poin", "jumlah_prestasi", "nama"], ascending=[False, False, True])
        .reset_index(drop=True)
    )
    grouped.insert(0, "ranking", range(1, len(grouped) + 1))
    return grouped[STUDENT_RANK_COLUMNS]


def dosen_ranking(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(DOSEN_RANK_COLUMNS)
    data = explode_dosen(frame)
    if data.empty:
        return _empty(DOSEN_RANK_COLUMNS)
    grouped = (
        data.groupby(["nuptk", "nama"], as_index=False)
        .agg(
            jumlah_prestasi=("prestasi_id", "nunique"),
            jumlah_mahasiswa=("nim", "nunique"),
            juara1=("peringkat", lambda values: int((values == "JUARA1").sum())),
            juara2=("peringkat", lambda values: int((values == "JUARA2").sum())),
            juara3=("peringkat", lambda values: int((values == "JUARA3").sum())),
            poin=("poin", "sum"),
        )
        .sort_values(["poin", "jumlah_prestasi", "jumlah_mahasiswa", "nama"], ascending=[False, False, False, True])
        .reset_index(drop=True)
    )
    grouped.insert(0, "ranking", range(1, len(grouped) + 1))
    return grouped[DOSEN_RANK_COLUMNS]


def category_summary(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["kategori_kode", "kategori", "jumlah_prestasi", "juara1", "juara2", "juara3", "poin"]
    if frame.empty:
        return _empty(columns)
    data = add_points(frame)
    grouped = (
        data.groupby(["kategori_kode", "kategori_nama"], as_index=False)
        .agg(
            jumlah_prestasi=("prestasi_id", "count"),
            juara1=("peringkat", lambda values: int((values == "JUARA1").sum())),
            juara2=("peringkat", lambda values: int((values == "JUARA2").sum())),
            juara3=("peringkat", lambda values: int((values == "JUARA3").sum())),
            poin=("poin", "sum"),
        )
        .sort_values(["jumlah_prestasi", "poin"], ascending=False)
        .reset_index(drop=True)
    )
    grouped["kategori"] = grouped.apply(
        lambda row: f"{CATEGORY_LABELS.get(row['kategori_kode'], row['kategori_nama'])} ({row['kategori_kode']})",
        axis=1,
    )
    return grouped[columns]


def recap_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    metrics = summary_metrics(frame)
    return pd.DataFrame(
        [
            ("Total prestasi", metrics["total_prestasi"]),
            ("Mahasiswa berprestasi", metrics["total_mahasiswa"]),
            ("Dosen pendamping", metrics["total_dosen"]),
            ("Total kompetisi", metrics["total_kompetisi"]),
            ("Prestasi nasional", metrics["nasional"]),
            ("Prestasi internasional", metrics["internasional"]),
            ("Prestasi provinsi", metrics["provinsi"]),
            ("Juara 1", metrics["juara1"]),
            ("Juara 2", metrics["juara2"]),
            ("Juara 3", metrics["juara3"]),
            ("Duplikat potensial", metrics["potensi_duplikat"]),
        ],
        columns=["Metrik", "Nilai"],
    )
