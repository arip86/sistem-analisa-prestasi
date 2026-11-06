from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from modules.analysis.common import (
    MONTH_LABELS,
    safe_pct_change,
    student_rows,
)

PERIOD_COLUMNS = [
    "periode",
    "jumlah_prestasi",
    "mahasiswa_unik",
    "kompetisi_unik",
    "selisih",
    "persentase",
]

MONTHLY_YEAR_COLUMNS = ["tahun", "bulan", "bulan_label", "jumlah_prestasi"]


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def normalize_granularity(granularity: str) -> str:
    value = (granularity or "").strip().lower()
    return "bulanan" if value.startswith("bulan") else "tahunan"


def _period_series(frame: pd.DataFrame, granularity: str) -> pd.Series:
    if granularity == "bulanan":
        dates = pd.to_datetime(frame.get("tgl_sertifikat"), errors="coerce")
        return dates.dt.strftime("%Y-%m")
    return frame.get("tahun", pd.Series(index=frame.index, dtype="object"))


def _period_range(frame: pd.DataFrame, granularity: str) -> List[str]:
    if granularity == "tahunan":
        years = pd.to_numeric(frame["tahun"], errors="coerce").dropna().astype(int)
        if years.empty:
            return []
        return [str(year) for year in range(int(years.min()), int(years.max()) + 1)]
    dates = pd.to_datetime(frame["tgl_sertifikat"], errors="coerce").dropna()
    if dates.empty:
        return []
    periods = pd.period_range(dates.min(), dates.max(), freq="M")
    return [period.strftime("%Y-%m") for period in periods]


def period_summary(frame: pd.DataFrame, granularity: str = "Tahunan") -> pd.DataFrame:
    if frame.empty:
        return _empty(PERIOD_COLUMNS)
    granularity = normalize_granularity(granularity)
    data = frame.copy()
    data["periode"] = _period_series(data, granularity)
    data = data[data["periode"].notna()].copy()
    if data.empty:
        return _empty(PERIOD_COLUMNS)
    data["periode"] = data["periode"].astype(str)
    counts = (
        data.groupby("periode", as_index=False)
        .agg(jumlah_prestasi=("prestasi_id", "nunique"))
    )
    students = student_rows(data)
    student_counts = (
        students.groupby("periode", as_index=False).agg(mahasiswa_unik=("nim", "nunique"))
        if not students.empty
        else _empty(["periode", "mahasiswa_unik"])
    )
    competitions = (
        data[["periode", "lomba", "tahun"]]
        .drop_duplicates()
        .groupby("periode", as_index=False)
        .size()
        .rename(columns={"size": "kompetisi_unik"})
    )
    result = counts.merge(student_counts, on="periode", how="left").merge(
        competitions, on="periode", how="left"
    )
    full_periods = _period_range(frame, granularity)
    if full_periods:
        result = (
            pd.DataFrame({"periode": full_periods})
            .merge(result, on="periode", how="left")
            .fillna({"jumlah_prestasi": 0, "mahasiswa_unik": 0, "kompetisi_unik": 0})
        )
    result[["jumlah_prestasi", "mahasiswa_unik", "kompetisi_unik"]] = result[
        ["jumlah_prestasi", "mahasiswa_unik", "kompetisi_unik"]
    ].astype(int)
    result = result.sort_values("periode").reset_index(drop=True)
    result["selisih"] = result["jumlah_prestasi"].diff()
    result["persentase"] = [
        safe_pct_change(current, previous)
        for current, previous in zip(
            result["jumlah_prestasi"], result["jumlah_prestasi"].shift(1)
        )
    ]
    return result[PERIOD_COLUMNS]


def monthly_by_year(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty(MONTHLY_YEAR_COLUMNS)
    data = frame.copy()
    data["tgl_sertifikat"] = pd.to_datetime(data["tgl_sertifikat"], errors="coerce")
    data = data.dropna(subset=["tgl_sertifikat"])
    if data.empty:
        return _empty(MONTHLY_YEAR_COLUMNS)
    data["tahun"] = data["tgl_sertifikat"].dt.year.astype(int)
    data["bulan"] = data["tgl_sertifikat"].dt.month.astype(int)
    counts = (
        data.groupby(["tahun", "bulan"], as_index=False)
        .agg(jumlah_prestasi=("prestasi_id", "nunique"))
    )
    years = sorted(data["tahun"].unique().tolist())
    full_index = pd.MultiIndex.from_product(
        [years, range(1, 13)], names=["tahun", "bulan"]
    )
    result = (
        pd.DataFrame(index=full_index)
        .reset_index()
        .merge(counts, on=["tahun", "bulan"], how="left")
        .fillna({"jumlah_prestasi": 0})
    )
    result["jumlah_prestasi"] = result["jumlah_prestasi"].astype(int)
    result["bulan_label"] = result["bulan"].map(MONTH_LABELS)
    return result.sort_values(["tahun", "bulan"]).reset_index(drop=True)[
        MONTHLY_YEAR_COLUMNS
    ]


def available_periods(frame: pd.DataFrame, granularity: str = "Tahunan") -> List[str]:
    return period_summary(frame, granularity)["periode"].dropna().tolist()


def trend_metrics(frame: pd.DataFrame, granularity: str = "Tahunan") -> Dict[str, Any]:
    summary = period_summary(frame, granularity)
    if summary.empty:
        return {
            "periode": 0,
            "periode_pertama": "-",
            "periode_terakhir": "-",
            "prestasi_pertama": 0,
            "prestasi_terakhir": 0,
            "pertumbuhan": None,
            "puncak": "-",
            "prestasi_puncak": 0,
            "rata_rata": 0.0,
        }
    first = summary.iloc[0]
    last = summary.iloc[-1]
    peak_index = summary["jumlah_prestasi"].idxmax()
    peak = summary.loc[peak_index]
    return {
        "periode": int(len(summary)),
        "periode_pertama": str(first["periode"]),
        "periode_terakhir": str(last["periode"]),
        "prestasi_pertama": int(first["jumlah_prestasi"]),
        "prestasi_terakhir": int(last["jumlah_prestasi"]),
        "pertumbuhan": safe_pct_change(
            last["jumlah_prestasi"], first["jumlah_prestasi"]
        ),
        "puncak": str(peak["periode"]),
        "prestasi_puncak": int(peak["jumlah_prestasi"]),
        "rata_rata": float(summary["jumlah_prestasi"].mean()),
    }


def period_comparison(
    frame: pd.DataFrame,
    granularity: str,
    period_a: str,
    period_b: str,
) -> Dict[str, Any]:
    summary = period_summary(frame, granularity)
    empty = {
        "periode_pertama": period_a,
        "periode_kedua": period_b,
        "jumlah_pertama": 0,
        "jumlah_kedua": 0,
        "selisih": 0,
        "persentase": None,
        "mahasiswa_pertama": 0,
        "mahasiswa_kedua": 0,
    }
    if summary.empty:
        return empty
    first = summary[summary["periode"] == str(period_a)]
    second = summary[summary["periode"] == str(period_b)]
    if first.empty or second.empty:
        return empty
    first_row = first.iloc[0]
    second_row = second.iloc[0]
    return {
        "periode_pertama": str(period_a),
        "periode_kedua": str(period_b),
        "jumlah_pertama": int(first_row["jumlah_prestasi"]),
        "jumlah_kedua": int(second_row["jumlah_prestasi"]),
        "selisih": int(second_row["jumlah_prestasi"] - first_row["jumlah_prestasi"]),
        "persentase": safe_pct_change(
            second_row["jumlah_prestasi"], first_row["jumlah_prestasi"]
        ),
        "mahasiswa_pertama": int(first_row["mahasiswa_unik"]),
        "mahasiswa_kedua": int(second_row["mahasiswa_unik"]),
    }


def period_label(period: str, granularity: str) -> str:
    if normalize_granularity(granularity) == "tahunan":
        return str(period)
    parsed = pd.to_datetime(f"{period}-01", errors="coerce")
    if pd.isna(parsed):
        return str(period)
    return parsed.strftime("%b %Y")
