from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from config.constants import LEVEL_POINTS, RANK_POINTS

MONTH_LABELS = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}

STUDENT_RANK_COLUMNS = [
    "ranking",
    "nim",
    "nama",
    "jumlah_prestasi",
    "poin",
    "jumlah_kategori",
    "jumlah_level",
    "juara1",
    "juara2",
    "juara3",
    "periode_pertama",
    "periode_terakhir",
]

LECTURER_RANK_COLUMNS = [
    "ranking",
    "nuptk",
    "nama",
    "jumlah_prestasi",
    "jumlah_mahasiswa",
    "poin",
    "jumlah_kategori",
    "jumlah_level",
    "juara1",
    "juara2",
    "juara3",
    "periode_pertama",
    "periode_terakhir",
]


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and not value.strip()


def split_multi(value: Any) -> List[str]:
    if _is_empty(value):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def join_unique(series: pd.Series, separator: str = ", ") -> str:
    values = []
    for value in series.dropna().tolist():
        text = str(value).strip()
        if text and text not in values:
            values.append(text)
    return separator.join(values)


def to_datetime_series(frame: pd.DataFrame) -> pd.Series:
    if "tgl_sertifikat" not in frame:
        return pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
    return pd.to_datetime(frame["tgl_sertifikat"], errors="coerce")


def add_points(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["poin"] = (
        data["level"].map(LEVEL_POINTS).fillna(1).astype(int)
        * data["peringkat"].map(RANK_POINTS).fillna(1).astype(int)
    )
    return data


def explode_people(
    frame: pd.DataFrame,
    id_column: str,
    name_column: str,
    id_alias: str,
    name_alias: str,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=list(frame.columns) + [id_alias, name_alias])
    records: List[Dict[str, Any]] = []
    for row in frame.to_dict("records"):
        identifiers = split_multi(row.get(id_column))
        names = split_multi(row.get(name_column))
        for index, identifier in enumerate(identifiers):
            record = dict(row)
            record[id_alias] = identifier
            record[name_alias] = names[index] if index < len(names) else (names[0] if names else "")
            records.append(record)
    result = pd.DataFrame(records)
    if result.empty:
        return pd.DataFrame(columns=list(frame.columns) + [id_alias, name_alias])
    return result.drop_duplicates(subset=["prestasi_id", id_alias]).reset_index(drop=True)


def student_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return explode_people(frame, "mahasiswa_nim", "mahasiswa_nama", "nim", "nama")


def lecturer_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return explode_people(frame, "dosen_nuptk", "dosen_nama", "nuptk", "nama")


def count_prestasi(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    return int(frame["prestasi_id"].nunique())


def count_students(frame: pd.DataFrame) -> int:
    rows = student_rows(frame)
    return int(rows["nim"].nunique()) if not rows.empty else 0


def count_lecturers(frame: pd.DataFrame) -> int:
    rows = lecturer_rows(frame)
    return int(rows["nuptk"].nunique()) if not rows.empty else 0


def count_competitions(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    return int(frame[["lomba", "tahun"]].drop_duplicates().shape[0])


def summary_counts(frame: pd.DataFrame) -> Dict[str, int]:
    return {
        "prestasi": count_prestasi(frame),
        "mahasiswa": count_students(frame),
        "dosen": count_lecturers(frame),
        "kompetisi": count_competitions(frame),
    }


def safe_pct_change(current: Any, previous: Any) -> Optional[float]:
    try:
        current_value = float(current)
        previous_value = float(previous)
    except (TypeError, ValueError):
        return None
    if pd.isna(current_value) or pd.isna(previous_value):
        return None
    if previous_value == 0:
        return 0.0 if current_value == 0 else None
    return (current_value - previous_value) / previous_value * 100


def period_span_months(first_value: Any, last_value: Any) -> int:
    first = pd.to_datetime(first_value, errors="coerce")
    last = pd.to_datetime(last_value, errors="coerce")
    if pd.isna(first) or pd.isna(last):
        return 1
    return (last.year - first.year) * 12 + (last.month - first.month) + 1


def month_label(month: Any) -> str:
    try:
        return MONTH_LABELS.get(int(month), str(month))
    except (TypeError, ValueError):
        return "-"


def _first_date(series: pd.Series) -> Optional[pd.Timestamp]:
    values = pd.to_datetime(series, errors="coerce").dropna()
    return values.min() if not values.empty else None


def _last_date(series: pd.Series) -> Optional[pd.Timestamp]:
    values = pd.to_datetime(series, errors="coerce").dropna()
    return values.max() if not values.empty else None


def _format_period(value: Any) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return "-"
    return parsed.strftime("%Y-%m")


def _count_ranks(series: pd.Series, rank_code: str) -> int:
    return int((series == rank_code).sum())


def student_count_ranking(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=STUDENT_RANK_COLUMNS)
    data = add_points(student_rows(frame))
    if data.empty:
        return pd.DataFrame(columns=STUDENT_RANK_COLUMNS)
    grouped = (
        data.groupby("nim", as_index=False)
        .agg(
            nama=("nama", "first"),
            jumlah_prestasi=("prestasi_id", "nunique"),
            poin=("poin", "sum"),
            jumlah_kategori=("kategori_kode", "nunique"),
            jumlah_level=("level", "nunique"),
            juara1=("peringkat", lambda values: _count_ranks(values, "JUARA1")),
            juara2=("peringkat", lambda values: _count_ranks(values, "JUARA2")),
            juara3=("peringkat", lambda values: _count_ranks(values, "JUARA3")),
            periode_pertama=("tgl_sertifikat", _first_date),
            periode_terakhir=("tgl_sertifikat", _last_date),
        )
        .sort_values(["jumlah_prestasi", "poin", "nama"], ascending=[False, False, True])
        .reset_index(drop=True)
    )
    grouped.insert(0, "ranking", range(1, len(grouped) + 1))
    grouped["periode_pertama"] = grouped["periode_pertama"].map(_format_period)
    grouped["periode_terakhir"] = grouped["periode_terakhir"].map(_format_period)
    return grouped[STUDENT_RANK_COLUMNS]


def lecturer_student_counts(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["nuptk", "jumlah_mahasiswa"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    records = []
    for row in frame.to_dict("records"):
        for nuptk in split_multi(row.get("dosen_nuptk")):
            for nim in split_multi(row.get("mahasiswa_nim")):
                records.append(
                    {
                        "nuptk": nuptk,
                        "nim": nim,
                        "prestasi_id": row.get("prestasi_id"),
                    }
                )
    if not records:
        return pd.DataFrame(columns=columns)
    data = pd.DataFrame(records).drop_duplicates(subset=["nuptk", "nim", "prestasi_id"])
    return (
        data.groupby("nuptk", as_index=False)
        .agg(jumlah_mahasiswa=("nim", "nunique"))
        .reset_index(drop=True)
    )


def lecturer_count_ranking(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=LECTURER_RANK_COLUMNS)
    data = add_points(lecturer_rows(frame))
    if data.empty:
        return pd.DataFrame(columns=LECTURER_RANK_COLUMNS)
    grouped = (
        data.groupby("nuptk", as_index=False)
        .agg(
            nama=("nama", "first"),
            jumlah_prestasi=("prestasi_id", "nunique"),
            poin=("poin", "sum"),
            jumlah_kategori=("kategori_kode", "nunique"),
            jumlah_level=("level", "nunique"),
            juara1=("peringkat", lambda values: _count_ranks(values, "JUARA1")),
            juara2=("peringkat", lambda values: _count_ranks(values, "JUARA2")),
            juara3=("peringkat", lambda values: _count_ranks(values, "JUARA3")),
            periode_pertama=("tgl_sertifikat", _first_date),
            periode_terakhir=("tgl_sertifikat", _last_date),
        )
    )
    student_counts = lecturer_student_counts(frame)
    grouped = grouped.merge(student_counts, on="nuptk", how="left").fillna({"jumlah_mahasiswa": 0})
    grouped["jumlah_mahasiswa"] = grouped["jumlah_mahasiswa"].astype(int)
    grouped = grouped.sort_values(
        ["jumlah_prestasi", "poin", "jumlah_mahasiswa", "nama"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    grouped.insert(0, "ranking", range(1, len(grouped) + 1))
    grouped["periode_pertama"] = grouped["periode_pertama"].map(_format_period)
    grouped["periode_terakhir"] = grouped["periode_terakhir"].map(_format_period)
    return grouped[LECTURER_RANK_COLUMNS]


def student_achievement_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    ranking = student_count_ranking(frame)
    columns = ["jumlah_prestasi", "jumlah_mahasiswa"]
    if ranking.empty:
        return pd.DataFrame(columns=columns)
    result = (
        ranking.groupby("jumlah_prestasi", as_index=False)
        .size()
        .rename(columns={"size": "jumlah_mahasiswa"})
        .sort_values("jumlah_prestasi")
        .reset_index(drop=True)
    )
    return result[columns]


def international_students(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "nim",
        "nama",
        "jumlah_prestasi",
        "lomba",
        "peringkat",
        "tahun",
        "dosen",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    international = frame[frame["level"] == "INT"]
    if international.empty:
        return pd.DataFrame(columns=columns)
    data = student_rows(international)
    grouped = (
        data.groupby("nim", as_index=False)
        .agg(
            nama=("nama", "first"),
            jumlah_prestasi=("prestasi_id", "nunique"),
            lomba=("lomba", join_unique),
            peringkat=("peringkat_label", join_unique),
            tahun=("tahun", join_unique),
            dosen=("dosen_nama", join_unique),
        )
        .sort_values(["jumlah_prestasi", "nama"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return grouped[columns]


def student_consistency(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "nim",
        "nama",
        "jumlah_prestasi",
        "tahun_aktif",
        "bulan_aktif",
        "rentang_bulan",
        "rasio_konsistensi",
        "periode_pertama",
        "periode_terakhir",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    data = student_rows(frame)
    if data.empty:
        return pd.DataFrame(columns=columns)
    data["periode"] = pd.to_datetime(data["tgl_sertifikat"], errors="coerce").dt.strftime("%Y-%m")
    grouped_rows = []
    for nim, group in data.groupby("nim", dropna=False):
        dates = pd.to_datetime(group["tgl_sertifikat"], errors="coerce").dropna()
        if dates.empty:
            continue
        nama = next((value for value in group["nama"].dropna().tolist() if str(value).strip()), "")
        active_months = int(group["periode"].dropna().nunique())
        active_years = int(dates.dt.year.nunique())
        span = period_span_months(dates.min(), dates.max())
        ratio = active_months / span if span else 0.0
        grouped_rows.append(
            {
                "nim": nim,
                "nama": nama,
                "jumlah_prestasi": int(group["prestasi_id"].nunique()),
                "tahun_aktif": active_years,
                "bulan_aktif": active_months,
                "rentang_bulan": span,
                "rasio_konsistensi": ratio,
                "periode_pertama": dates.min().strftime("%Y-%m"),
                "periode_terakhir": dates.max().strftime("%Y-%m"),
            }
        )
    result = pd.DataFrame(grouped_rows, columns=columns)
    if result.empty:
        return result
    return result.sort_values(
        ["rasio_konsistensi", "bulan_aktif", "jumlah_prestasi", "nama"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)


def individual_group_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["kelompok", "jumlah_prestasi", "jumlah_mahasiswa"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    data = frame.copy()
    data["kelompok"] = data["kelompok_prestasi"].fillna("Tidak tercatat")
    rows = student_rows(data)
    grouped = (
        data.groupby("kelompok", as_index=False)
        .agg(jumlah_prestasi=("prestasi_id", "nunique"))
    )
    students = rows.groupby("kelompok", as_index=False).agg(jumlah_mahasiswa=("nim", "nunique"))
    result = grouped.merge(students, on="kelompok", how="left").fillna({"jumlah_mahasiswa": 0})
    result["jumlah_mahasiswa"] = result["jumlah_mahasiswa"].astype(int)
    return result.sort_values("jumlah_prestasi", ascending=False).reset_index(drop=True)[columns]


def student_metrics(frame: pd.DataFrame) -> Dict[str, int]:
    ranking = student_count_ranking(frame)
    international = frame[frame["level"] == "INT"] if not frame.empty else frame
    groups = individual_group_distribution(frame)
    return {
        "total_mahasiswa": int(len(ranking)),
        "mahasiswa_multiple": int((ranking["jumlah_prestasi"] >= 2).sum()) if not ranking.empty else 0,
        "mahasiswa_internasional": int(count_students(international)),
        "prestasi_individu": int(groups.loc[groups["kelompok"] == "INDIVIDU", "jumlah_prestasi"].sum()) if not groups.empty else 0,
        "prestasi_kelompok": int(groups.loc[groups["kelompok"] == "KELOMPOK", "jumlah_prestasi"].sum()) if not groups.empty else 0,
    }


def lecturer_student_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["jumlah_mahasiswa", "jumlah_dosen"]
    ranking = lecturer_count_ranking(frame)
    if ranking.empty:
        return pd.DataFrame(columns=columns)
    return (
        ranking.groupby("jumlah_mahasiswa", as_index=False)
        .size()
        .rename(columns={"size": "jumlah_dosen"})
        .sort_values("jumlah_mahasiswa")
        .reset_index(drop=True)[columns]
    )


def lecturer_distribution(frame: pd.DataFrame, dimension: str, top_n: int = 10) -> pd.DataFrame:
    columns = ["dosen", "dosen_label", dimension, "jumlah_prestasi"]
    if frame.empty or dimension not in frame.columns:
        return pd.DataFrame(columns=columns)
    data = lecturer_rows(frame)
    if data.empty:
        return pd.DataFrame(columns=columns)
    data["dosen_label"] = data["nama"]
    totals = (
        data.groupby("dosen_label")["prestasi_id"]
        .nunique()
        .sort_values(ascending=False)
        .head(top_n)
    )
    selected = data[data["dosen_label"].isin(totals.index)].copy()
    grouped = (
        selected.groupby(["dosen_label", dimension], as_index=False)
        .agg(jumlah_prestasi=("prestasi_id", "nunique"))
        .sort_values(["dosen_label", "jumlah_prestasi"], ascending=[True, False])
    )
    grouped["dosen"] = grouped["dosen_label"]
    return grouped[columns]


def lecturer_metrics(frame: pd.DataFrame) -> Dict[str, Any]:
    ranking = lecturer_count_ranking(frame)
    if ranking.empty:
        return {
            "total_dosen": 0,
            "rata_mahasiswa": 0.0,
            "dosen_multiple": 0,
            "mahasiswa_terbanyak": 0,
        }
    return {
        "total_dosen": int(len(ranking)),
        "rata_mahasiswa": float(ranking["jumlah_mahasiswa"].mean()),
        "dosen_multiple": int((ranking["jumlah_prestasi"] >= 2).sum()),
        "mahasiswa_terbanyak": int(ranking["jumlah_mahasiswa"].max()),
    }
