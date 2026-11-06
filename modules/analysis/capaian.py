from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from config.constants import CATEGORY_SHORT_LABELS, LEVEL_LABELS, PERINGKAT_LABELS
from modules.analysis.common import (
    add_points,
    count_competitions,
    count_lecturers,
    count_prestasi,
    count_students,
    lecturer_count_ranking,
    student_rows,
)

YEAR_COLUMNS = [
    "tahun",
    "jumlah_prestasi",
    "mahasiswa_unik",
    "kompetisi_unik",
    "poin",
]

CATEGORY_COLUMNS = [
    "kategori_kode",
    "kategori",
    "jumlah_prestasi",
    "mahasiswa_unik",
    "kompetisi_unik",
    "level_unik",
    "poin",
]

LEVEL_COLUMNS = [
    "level",
    "level_label",
    "jumlah_prestasi",
    "mahasiswa_unik",
    "kompetisi_unik",
    "poin",
]

RANK_COLUMNS = ["peringkat", "peringkat_label", "jumlah_prestasi"]


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def summary_metrics(frame: pd.DataFrame) -> Dict[str, Any]:
    years = pd.to_numeric(frame.get("tahun"), errors="coerce").dropna() if not frame.empty else pd.Series(dtype="float64")
    data = add_points(frame) if not frame.empty else frame
    return {
        "total_prestasi": count_prestasi(frame),
        "total_mahasiswa": count_students(frame),
        "total_dosen": count_lecturers(frame),
        "total_kompetisi": count_competitions(frame),
        "total_poin": int(data["poin"].sum()) if not data.empty else 0,
        "tahun_awal": int(years.min()) if not years.empty else None,
        "tahun_akhir": int(years.max()) if not years.empty else None,
        "jumlah_tahun": int(years.nunique()) if not years.empty else 0,
    }


def yearly_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(YEAR_COLUMNS)
    data = add_points(frame.dropna(subset=["tahun"]))
    if data.empty:
        return _empty(YEAR_COLUMNS)
    grouped = data.groupby("tahun", as_index=False).agg(
        jumlah_prestasi=("prestasi_id", "nunique"),
        poin=("poin", "sum"),
    )
    students = student_rows(data)
    student_counts = (
        students.groupby("tahun", as_index=False).agg(mahasiswa_unik=("nim", "nunique"))
        if not students.empty
        else _empty(["tahun", "mahasiswa_unik"])
    )
    competitions = (
        data[["tahun", "lomba"]]
        .drop_duplicates()
        .groupby("tahun", as_index=False)
        .size()
        .rename(columns={"size": "kompetisi_unik"})
    )
    result = grouped.merge(student_counts, on="tahun", how="left").merge(
        competitions, on="tahun", how="left"
    )
    result[["mahasiswa_unik", "kompetisi_unik"]] = result[
        ["mahasiswa_unik", "kompetisi_unik"]
    ].fillna(0).astype(int)
    result["tahun"] = result["tahun"].astype(int)
    return result.sort_values("tahun").reset_index(drop=True)[YEAR_COLUMNS]


def category_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(CATEGORY_COLUMNS)
    data = add_points(frame)
    grouped = data.groupby("kategori_kode", as_index=False).agg(
        kategori_nama=("kategori_nama", "first"),
        jumlah_prestasi=("prestasi_id", "nunique"),
        level_unik=("level", "nunique"),
        poin=("poin", "sum"),
    )
    students = student_rows(data)
    student_counts = (
        students.groupby("kategori_kode", as_index=False).agg(mahasiswa_unik=("nim", "nunique"))
        if not students.empty
        else _empty(["kategori_kode", "mahasiswa_unik"])
    )
    competitions = (
        data[["kategori_kode", "lomba", "tahun"]]
        .drop_duplicates()
        .groupby("kategori_kode", as_index=False)
        .size()
        .rename(columns={"size": "kompetisi_unik"})
    )
    result = grouped.merge(student_counts, on="kategori_kode", how="left").merge(
        competitions, on="kategori_kode", how="left"
    )
    result[["mahasiswa_unik", "kompetisi_unik"]] = result[
        ["mahasiswa_unik", "kompetisi_unik"]
    ].fillna(0).astype(int)
    result["kategori"] = result.apply(
        lambda row: f"{CATEGORY_SHORT_LABELS.get(row['kategori_kode'], row['kategori_nama'] or row['kategori_kode'])} ({row['kategori_kode']})",
        axis=1,
    )
    return (
        result.sort_values(["jumlah_prestasi", "poin"], ascending=False)
        .reset_index(drop=True)[CATEGORY_COLUMNS]
    )


def level_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(LEVEL_COLUMNS)
    data = add_points(frame)
    grouped = data.groupby("level", as_index=False).agg(
        jumlah_prestasi=("prestasi_id", "nunique"),
        poin=("poin", "sum"),
    )
    students = student_rows(data)
    student_counts = (
        students.groupby("level", as_index=False).agg(mahasiswa_unik=("nim", "nunique"))
        if not students.empty
        else _empty(["level", "mahasiswa_unik"])
    )
    competitions = (
        data[["level", "lomba", "tahun"]]
        .drop_duplicates()
        .groupby("level", as_index=False)
        .size()
        .rename(columns={"size": "kompetisi_unik"})
    )
    result = grouped.merge(student_counts, on="level", how="left").merge(
        competitions, on="level", how="left"
    )
    result[["mahasiswa_unik", "kompetisi_unik"]] = result[
        ["mahasiswa_unik", "kompetisi_unik"]
    ].fillna(0).astype(int)
    result["level_label"] = result["level"].map(LEVEL_LABELS).fillna(result["level"])
    order = {code: index for index, code in enumerate(["INT", "NAS", "PROV", "KAB", "KOTA"])}
    result["urutan"] = result["level"].map(order).fillna(99)
    return (
        result.sort_values(["urutan", "jumlah_prestasi"], ascending=[True, False])
        .drop(columns=["urutan"])
        .reset_index(drop=True)[LEVEL_COLUMNS]
    )


def rank_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(RANK_COLUMNS)
    data = frame.copy()
    data["peringkat_label"] = data["peringkat"].map(PERINGKAT_LABELS).fillna(data["peringkat"])
    result = (
        data.groupby(["peringkat", "peringkat_label"], as_index=False)
        .agg(jumlah_prestasi=("prestasi_id", "nunique"))
    )
    order = {
        code: index
        for index, code in enumerate(
            ["JUARA1", "JUARA2", "JUARA3", "HARAPAN1", "HARAPAN2", "HARAPAN3"]
        )
    }
    result["urutan"] = result["peringkat"].map(order).fillna(99)
    return (
        result.sort_values(["urutan", "jumlah_prestasi"], ascending=[True, False])
        .drop(columns=["urutan"])
        .reset_index(drop=True)[RANK_COLUMNS]
    )


def category_level_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["kategori_kode", "kategori", "level", "level_label", "jumlah_prestasi"]
    if frame.empty:
        return _empty(columns)
    data = frame.copy()
    data["kategori"] = data["kategori_kode"].map(CATEGORY_SHORT_LABELS).fillna(
        data["kategori_nama"]
    )
    data["level_label"] = data["level"].map(LEVEL_LABELS).fillna(data["level"])
    result = (
        data.groupby(
            ["kategori_kode", "kategori", "level", "level_label"], as_index=False
        )
        .agg(jumlah_prestasi=("prestasi_id", "nunique"))
        .sort_values(["kategori", "jumlah_prestasi"], ascending=[True, False])
    )
    return result[columns]


def level_yearly_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["tahun", "level", "level_label", "jumlah_prestasi"]
    if frame.empty:
        return _empty(columns)
    data = frame.dropna(subset=["tahun"]).copy()
    if data.empty:
        return _empty(columns)
    data["level_label"] = data["level"].map(LEVEL_LABELS).fillna(data["level"])
    result = (
        data.groupby(["tahun", "level", "level_label"], as_index=False)
        .agg(jumlah_prestasi=("prestasi_id", "nunique"))
        .sort_values(["tahun", "level"])
    )
    result["tahun"] = result["tahun"].astype(int)
    return result[columns]


def lecturer_student_summary(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["nuptk", "dosen", "jumlah_prestasi", "jumlah_mahasiswa"]
    if frame.empty:
        return _empty(columns)
    ranking = lecturer_count_ranking(frame)
    if ranking.empty:
        return _empty(columns)
    result = ranking.rename(columns={"nama": "dosen"})
    return result[columns]
