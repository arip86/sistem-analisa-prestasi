from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import render_kpi_grid
from components.data_access import load_prestasi
from components.filters import apply_filters, filter_summary_text, render_filters
from components.layout import format_number, missing_data_notice, page_header, section_title
from modules.analytics import (
    category_summary,
    dosen_ranking,
    level_counts,
    student_ranking,
    summary_metrics,
)
from modules.privacy import mask_nim


def _student_table(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    if "nim" in data.columns:
        data["nim"] = data["nim"].map(mask_nim)
    return data.rename(
        columns={
            "ranking": "Peringkat",
            "nim": "NIM",
            "nama": "Nama Mahasiswa",
            "jumlah_prestasi": "Jumlah Prestasi",
            "juara1": "Juara 1",
            "juara2": "Juara 2",
            "juara3": "Juara 3",
            "poin": "Poin",
        }
    )


def _dosen_table(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.drop(columns=["nuptk"], errors="ignore")
    return data.rename(
        columns={
            "ranking": "Peringkat",
            "nama": "Nama Dosen",
            "jumlah_prestasi": "Jumlah Prestasi",
            "jumlah_mahasiswa": "Jumlah Mahasiswa",
            "juara1": "Juara 1",
            "juara2": "Juara 2",
            "juara3": "Juara 3",
            "poin": "Poin",
        }
    )


def render() -> None:
    page_header(
        "Laporan",
        "Tinjau laporan prestasi terfilter dalam bentuk ringkasan dan peringkat.",
    )
    frame, error = load_prestasi()
    if error:
        st.error(f"Data belum dapat dimuat: {error}")
        return
    if frame.empty:
        missing_data_notice()
        return

    filters = render_filters(frame, "report")
    data = apply_filters(frame, filters)
    filter_text = filter_summary_text(filters)
    st.caption(f"{format_number(len(data))} prestasi pada laporan. Filter: {filter_text}")
    if data.empty:
        st.warning("Tidak ada prestasi yang sesuai dengan filter.")
        return

    metrics = summary_metrics(data)
    render_kpi_grid(
        [
            {
                "title": "Total Prestasi",
                "value": format_number(metrics["total_prestasi"]),
                "subtitle": "Baris pada laporan",
                "color": "#2F80ED",
            },
            {
                "title": "Mahasiswa",
                "value": format_number(metrics["total_mahasiswa"]),
                "subtitle": "NIM unik",
                "color": "#1E4E8C",
            },
            {
                "title": "Dosen",
                "value": format_number(metrics["total_dosen"]),
                "subtitle": "Dosen unik",
                "color": "#1F9D55",
            },
            {
                "title": "Juara 1",
                "value": format_number(metrics["juara1"]),
                "subtitle": "Prestasi peringkat pertama",
                "color": "#D97706",
            },
        ]
    )

    left, right = st.columns(2)
    with left:
        section_title("Rekap Kategori")
        st.dataframe(
            category_summary(data).rename(
                columns={
                    "kategori_kode": "Kode",
                    "kategori": "Kategori",
                    "jumlah_prestasi": "Jumlah Prestasi",
                    "juara1": "Juara 1",
                    "juara2": "Juara 2",
                    "juara3": "Juara 3",
                    "poin": "Poin",
                }
            ),
            width="stretch",
            hide_index=True,
        )
    with right:
        section_title("Sebaran Level")
        st.dataframe(
            level_counts(data).rename(
                columns={"level": "Kode", "level_label": "Level", "jumlah": "Jumlah Prestasi"}
            ),
            width="stretch",
            hide_index=True,
        )
    left, right = st.columns(2)
    with left:
        section_title("10 Mahasiswa dengan Poin Tertinggi")
        st.dataframe(
            _student_table(student_ranking(data).head(10)),
            width="stretch",
            hide_index=True,
        )
    with right:
        section_title("10 Dosen dengan Poin Tertinggi")
        st.dataframe(
            _dosen_table(dosen_ranking(data).head(10)),
            width="stretch",
            hide_index=True,
        )
