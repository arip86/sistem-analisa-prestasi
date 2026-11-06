from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from config.constants import CATEGORY_SHORT_LABELS, LEVEL_LABELS, PERINGKAT_LABELS
from modules.analytics import filter_data


def _date_bounds(frame: pd.DataFrame) -> tuple[Optional[date], Optional[date]]:
    if frame.empty or "tgl_sertifikat" not in frame:
        return None, None
    dates = frame["tgl_sertifikat"].dropna()
    if dates.empty:
        return None, None
    return dates.min().date(), dates.max().date()


def render_filters(
    frame: pd.DataFrame,
    key_prefix: str,
    show_date: bool = True,
    show_year: bool = True,
    show_duplicate: bool = False,
    expanded: bool = False,
    columns: int = 3,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "start_date": None,
        "end_date": None,
        "kategori": [],
        "level": [],
        "peringkat": [],
        "tahun": [],
        "only_duplicate": False,
    }
    if frame.empty:
        return result

    with st.expander("Filter data", expanded=expanded):
        rows = []

        def column_at(index: int):
            row_index, column_index = divmod(index, max(1, columns))
            while len(rows) <= row_index:
                rows.append(st.columns(max(1, columns)))
            return rows[row_index][column_index]

        current = 0

        if show_date:
            start_bound, end_bound = _date_bounds(frame)
            if start_bound and end_bound:
                with column_at(current):
                    selected = st.date_input(
                        "Periode sertifikat",
                        value=(start_bound, end_bound),
                        min_value=start_bound,
                        max_value=end_bound,
                        key=f"{key_prefix}_periode",
                        format="DD/MM/YYYY",
                    )
                current += 1
                if isinstance(selected, (tuple, list)) and len(selected) == 2:
                    result["start_date"], result["end_date"] = selected
                elif isinstance(selected, date):
                    result["start_date"] = selected
                    result["end_date"] = selected

        if show_year:
            years = sorted(
                int(year)
                for year in frame["tahun"].dropna().unique().tolist()
                if str(year).isdigit()
            )
            with column_at(current):
                result["tahun"] = st.multiselect(
                    "Tahun",
                    options=years,
                    key=f"{key_prefix}_tahun",
                )
            current += 1

        category_codes = [
            code for code in frame["kategori_kode"].dropna().unique().tolist() if code
        ]
        category_codes.sort()
        with column_at(current):
            result["kategori"] = st.multiselect(
                "Kategori",
                options=category_codes,
                format_func=lambda code: f"{CATEGORY_SHORT_LABELS.get(code, code)} ({code})",
                key=f"{key_prefix}_kategori",
            )
        current += 1

        level_codes = [
            code
            for code in ["INT", "NAS", "PROV", "KAB", "KOTA"]
            if code in set(frame["level"].dropna().unique().tolist())
        ]
        with column_at(current):
            result["level"] = st.multiselect(
                "Level",
                options=level_codes,
                format_func=lambda code: LEVEL_LABELS.get(code, code),
                key=f"{key_prefix}_level",
            )
        current += 1

        rank_codes = [
            code
            for code in ["JUARA1", "JUARA2", "JUARA3", "HARAPAN1", "HARAPAN2", "HARAPAN3"]
            if code in set(frame["peringkat"].dropna().unique().tolist())
        ]
        with column_at(current):
            result["peringkat"] = st.multiselect(
                "Peringkat",
                options=rank_codes,
                format_func=lambda code: PERINGKAT_LABELS.get(code, code),
                key=f"{key_prefix}_peringkat",
            )
        current += 1

        if show_duplicate:
            with column_at(current):
                result["only_duplicate"] = st.checkbox(
                    "Tampilkan hanya duplikat potensial",
                    key=f"{key_prefix}_duplikat",
                )

    return result


def apply_filters(frame: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    data = filter_data(
        frame,
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
        kategori=filters.get("kategori") or None,
        level=filters.get("level") or None,
        peringkat=filters.get("peringkat") or None,
        tahun=filters.get("tahun") or None,
    )
    if filters.get("only_duplicate") and not data.empty:
        data = data[data["is_duplicate_suspect"]].reset_index(drop=True)
    return data


def filter_summary_text(filters: Dict[str, Any]) -> str:
    parts = []
    if filters.get("start_date") and filters.get("end_date"):
        parts.append(
            f"{filters['start_date'].strftime('%d/%m/%Y')} - {filters['end_date'].strftime('%d/%m/%Y')}"
        )
    if filters.get("kategori"):
        parts.append("Kategori: " + ", ".join(filters["kategori"]))
    if filters.get("level"):
        parts.append("Level: " + ", ".join(LEVEL_LABELS.get(item, item) for item in filters["level"]))
    if filters.get("peringkat"):
        parts.append("Peringkat: " + ", ".join(PERINGKAT_LABELS.get(item, item) for item in filters["peringkat"]))
    if filters.get("tahun"):
        parts.append("Tahun: " + ", ".join(str(item) for item in filters["tahun"]))
    if filters.get("only_duplicate"):
        parts.append("Hanya duplikat potensial")
    return " | ".join(parts) if parts else "Semua data"
