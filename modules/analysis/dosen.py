from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from modules.analysis.common import (
    lecturer_count_ranking,
    lecturer_distribution,
    lecturer_metrics,
    lecturer_student_distribution,
)


def ranking(frame: pd.DataFrame) -> pd.DataFrame:
    return lecturer_count_ranking(frame)


def metrics(frame: pd.DataFrame) -> Dict[str, Any]:
    return lecturer_metrics(frame)


def top_lecturers(frame: pd.DataFrame, limit: int = 10, metric: str = "count") -> pd.DataFrame:
    data = lecturer_count_ranking(frame)
    if data.empty:
        return data
    if metric == "points":
        return data.sort_values(
            ["poin", "jumlah_prestasi", "jumlah_mahasiswa", "nama"],
            ascending=[False, False, False, True],
        ).head(limit)
    if metric == "students":
        return data.sort_values(
            ["jumlah_mahasiswa", "jumlah_prestasi", "nama"],
            ascending=[False, False, True],
        ).head(limit)
    return data.head(limit)


def distribution(frame: pd.DataFrame, dimension: str = "level_label", top_n: int = 10) -> pd.DataFrame:
    return lecturer_distribution(frame, dimension=dimension, top_n=top_n)


def student_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    return lecturer_student_distribution(frame)
