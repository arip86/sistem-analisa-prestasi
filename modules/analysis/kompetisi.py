from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from config.constants import LEVEL_LABELS
from modules.analysis.common import (
    count_competitions,
    count_prestasi,
    count_students,
    join_unique,
    student_rows,
)

COMPETITION_COLUMNS = [
    "lomba",
    "tahun",
    "level",
    "kategori",
    "penyelenggara",
    "cabang",
    "jumlah_prestasi",
    "jumlah_mahasiswa",
]

LEVEL_COLUMNS = [
    "level",
    "level_label",
    "jumlah_prestasi",
    "jumlah_kompetisi",
    "jumlah_lomba",
    "jumlah_mahasiswa",
]

ORGANIZER_COLUMNS = [
    "penyelenggara",
    "jumlah_prestasi",
    "jumlah_kompetisi",
    "jumlah_lomba",
    "jumlah_mahasiswa",
]

BRANCH_COLUMNS = [
    "cabang",
    "jumlah_prestasi",
    "jumlah_kompetisi",
    "jumlah_lomba",
    "jumlah_mahasiswa",
]

REPEAT_COLUMNS = [
    "lomba",
    "jumlah_edisi",
    "jumlah_prestasi",
    "tahun_pertama",
    "tahun_terakhir",
]


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["tahun"] = data["tahun"].fillna("Tidak tercatat").astype(str)
    data["level_label"] = data["level"].map(LEVEL_LABELS).fillna(data["level"])
    return data


def competition_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(COMPETITION_COLUMNS)
    data = _prepare(frame)
    grouped = (
        data.groupby(["lomba", "tahun"], as_index=False)
        .agg(
            level=("level_label", join_unique),
            kategori=("kategori_nama", join_unique),
            penyelenggara=("penyelenggara", join_unique),
            cabang=("cabang", join_unique),
            jumlah_prestasi=("prestasi_id", "nunique"),
        )
    )
    students = student_rows(data)
    student_counts = (
        students.groupby(["lomba", "tahun"], as_index=False)
        .agg(jumlah_mahasiswa=("nim", "nunique"))
        if not students.empty
        else _empty(["lomba", "tahun", "jumlah_mahasiswa"])
    )
    result = grouped.merge(student_counts, on=["lomba", "tahun"], how="left").fillna(
        {"jumlah_mahasiswa": 0}
    )
    result["jumlah_mahasiswa"] = result["jumlah_mahasiswa"].astype(int)
    return (
        result.sort_values(
            ["jumlah_prestasi", "tahun", "lomba"], ascending=[False, False, True]
        )
        .reset_index(drop=True)[COMPETITION_COLUMNS]
    )


def level_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(LEVEL_COLUMNS)
    data = _prepare(frame)
    grouped = (
        data.groupby(["level", "level_label"], as_index=False)
        .agg(jumlah_prestasi=("prestasi_id", "nunique"))
    )
    editions = (
        data[["level", "lomba", "tahun"]]
        .drop_duplicates()
        .groupby("level", as_index=False)
        .size()
        .rename(columns={"size": "jumlah_kompetisi"})
    )
    titles = (
        data[["level", "lomba"]]
        .drop_duplicates()
        .groupby("level", as_index=False)
        .size()
        .rename(columns={"size": "jumlah_lomba"})
    )
    students = student_rows(data)
    student_counts = (
        students.groupby("level", as_index=False).agg(jumlah_mahasiswa=("nim", "nunique"))
        if not students.empty
        else _empty(["level", "jumlah_mahasiswa"])
    )
    result = (
        grouped.merge(editions, on="level", how="left")
        .merge(titles, on="level", how="left")
        .merge(student_counts, on="level", how="left")
        .fillna({"jumlah_kompetisi": 0, "jumlah_lomba": 0, "jumlah_mahasiswa": 0})
    )
    result[["jumlah_kompetisi", "jumlah_lomba", "jumlah_mahasiswa"]] = result[
        ["jumlah_kompetisi", "jumlah_lomba", "jumlah_mahasiswa"]
    ].astype(int)
    order = {code: index for index, code in enumerate(["INT", "NAS", "PROV", "KAB", "KOTA"])}
    result["urutan"] = result["level"].map(order).fillna(99)
    return (
        result.sort_values(["urutan", "jumlah_prestasi"], ascending=[True, False])
        .drop(columns=["urutan"])
        .reset_index(drop=True)[LEVEL_COLUMNS]
    )


def organizer_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(ORGANIZER_COLUMNS)
    data = _prepare(frame)
    grouped = data.groupby("penyelenggara", as_index=False).agg(
        jumlah_prestasi=("prestasi_id", "nunique"),
        jumlah_lomba=("lomba", "nunique"),
    )
    editions = (
        data[["penyelenggara", "lomba", "tahun"]]
        .drop_duplicates()
        .groupby("penyelenggara", as_index=False)
        .size()
        .rename(columns={"size": "jumlah_kompetisi"})
    )
    students = student_rows(data)
    student_counts = (
        students.groupby("penyelenggara", as_index=False).agg(
            jumlah_mahasiswa=("nim", "nunique")
        )
        if not students.empty
        else _empty(["penyelenggara", "jumlah_mahasiswa"])
    )
    result = (
        grouped.merge(editions, on="penyelenggara", how="left")
        .merge(student_counts, on="penyelenggara", how="left")
        .fillna({"jumlah_kompetisi": 0, "jumlah_mahasiswa": 0})
    )
    result[["jumlah_kompetisi", "jumlah_mahasiswa"]] = result[
        ["jumlah_kompetisi", "jumlah_mahasiswa"]
    ].astype(int)
    return (
        result.sort_values(
            ["jumlah_prestasi", "jumlah_kompetisi", "penyelenggara"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)[ORGANIZER_COLUMNS]
    )


def branch_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(BRANCH_COLUMNS)
    data = _prepare(frame)
    grouped = data.groupby("cabang", as_index=False).agg(
        jumlah_prestasi=("prestasi_id", "nunique"),
        jumlah_lomba=("lomba", "nunique"),
    )
    editions = (
        data[["cabang", "lomba", "tahun"]]
        .drop_duplicates()
        .groupby("cabang", as_index=False)
        .size()
        .rename(columns={"size": "jumlah_kompetisi"})
    )
    students = student_rows(data)
    student_counts = (
        students.groupby("cabang", as_index=False).agg(jumlah_mahasiswa=("nim", "nunique"))
        if not students.empty
        else _empty(["cabang", "jumlah_mahasiswa"])
    )
    result = (
        grouped.merge(editions, on="cabang", how="left")
        .merge(student_counts, on="cabang", how="left")
        .fillna({"jumlah_kompetisi": 0, "jumlah_mahasiswa": 0})
    )
    result[["jumlah_kompetisi", "jumlah_mahasiswa"]] = result[
        ["jumlah_kompetisi", "jumlah_mahasiswa"]
    ].astype(int)
    return (
        result.sort_values(
            ["jumlah_prestasi", "jumlah_kompetisi", "cabang"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)[BRANCH_COLUMNS]
    )


def recurring_competitions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(REPEAT_COLUMNS)
    data = _prepare(frame)
    yearly = data[data["tahun"] != "Tidak tercatat"]
    if yearly.empty:
        return _empty(REPEAT_COLUMNS)
    result = yearly.groupby("lomba", as_index=False).agg(
        jumlah_edisi=("tahun", "nunique"),
        jumlah_prestasi=("prestasi_id", "nunique"),
        tahun_pertama=("tahun", "min"),
        tahun_terakhir=("tahun", "max"),
    )
    return (
        result.sort_values(
            ["jumlah_edisi", "jumlah_prestasi", "lomba"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)[REPEAT_COLUMNS]
    )


def metrics(frame: pd.DataFrame) -> Dict[str, Any]:
    table = competition_table(frame)
    organizers = organizer_summary(frame)
    branches = branch_summary(frame)
    top = table.iloc[0] if not table.empty else None
    return {
        "total_kompetisi": count_competitions(frame),
        "total_lomba": int(frame["lomba"].nunique()) if not frame.empty else 0,
        "total_penyelenggara": int(frame["penyelenggara"].nunique()) if not frame.empty else 0,
        "total_cabang": int(frame["cabang"].nunique()) if not frame.empty else 0,
        "total_prestasi": count_prestasi(frame),
        "total_mahasiswa": count_students(frame),
        "kompetisi_terbanyak": f"{top['lomba']} ({top['tahun']})" if top is not None else "-",
        "prestasi_terbanyak": int(top["jumlah_prestasi"]) if top is not None else 0,
        "penyelenggara_teratas": organizers.iloc[0]["penyelenggara"] if not organizers.empty else "-",
        "cabang_teratas": branches.iloc[0]["cabang"] if not branches.empty else "-",
    }
