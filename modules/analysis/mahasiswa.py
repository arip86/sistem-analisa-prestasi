from __future__ import annotations

from typing import Dict

import pandas as pd

from modules.analysis.common import (
    individual_group_distribution,
    international_students,
    split_multi,
    student_achievement_distribution,
    student_consistency,
    student_count_ranking,
    student_metrics,
    student_rows,
)


def ranking(frame: pd.DataFrame) -> pd.DataFrame:
    return student_count_ranking(frame)


def metrics(frame: pd.DataFrame) -> Dict[str, int]:
    return student_metrics(frame)


def top_students(frame: pd.DataFrame, limit: int = 10, metric: str = "count") -> pd.DataFrame:
    data = student_count_ranking(frame)
    if data.empty:
        return data
    if metric == "points":
        return data.sort_values(
            ["poin", "jumlah_prestasi", "nama"], ascending=[False, False, True]
        ).head(limit)
    return data.head(limit)


def top_consistency(
    frame: pd.DataFrame,
    limit: int = 10,
    minimum_prestasi: int = 2,
) -> pd.DataFrame:
    data = student_consistency(frame)
    if data.empty:
        return data
    data = data[data["jumlah_prestasi"] >= minimum_prestasi]
    return data.head(limit).reset_index(drop=True)


def consistency(frame: pd.DataFrame) -> pd.DataFrame:
    return student_consistency(frame)


def distribution(frame: pd.DataFrame) -> pd.DataFrame:
    return student_achievement_distribution(frame)


def group_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    return individual_group_distribution(frame)


def international(frame: pd.DataFrame) -> pd.DataFrame:
    return international_students(frame)


def student_activity(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "nim",
        "nama",
        "jumlah_prestasi",
        "tahun_pertama",
        "tahun_terakhir",
        "jumlah_kategori",
        "jumlah_level",
        "jumlah_dosen",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    data = student_rows(frame)
    if data.empty:
        return pd.DataFrame(columns=columns)
    grouped = (
        data.groupby("nim", as_index=False)
        .agg(
            nama=("nama", "first"),
            jumlah_prestasi=("prestasi_id", "nunique"),
            jumlah_kategori=("kategori_kode", "nunique"),
            jumlah_level=("level", "nunique"),
            tahun_pertama=("tahun", "min"),
            tahun_terakhir=("tahun", "max"),
        )
        .sort_values(["jumlah_prestasi", "nama"], ascending=[False, True])
    )
    lecturer_records = []
    for row in frame.to_dict("records"):
        nims = split_multi(row.get("mahasiswa_nim"))
        nuptks = split_multi(row.get("dosen_nuptk"))
        for nim in nims:
            for nuptk in nuptks:
                lecturer_records.append({"nim": nim, "nuptk": nuptk})
    if lecturer_records:
        lecturer_data = pd.DataFrame(lecturer_records).drop_duplicates()
        lecturer_counts = (
            lecturer_data.groupby("nim", as_index=False)
            .agg(jumlah_dosen=("nuptk", "nunique"))
        )
        grouped = grouped.merge(lecturer_counts, on="nim", how="left")
    if "jumlah_dosen" not in grouped:
        grouped["jumlah_dosen"] = 0
    grouped[["tahun_pertama", "tahun_terakhir"]] = grouped[
        ["tahun_pertama", "tahun_terakhir"]
    ].fillna("-")
    return grouped.fillna({"jumlah_dosen": 0})[columns]
