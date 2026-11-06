from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from components.cards import render_kpi_grid
from components.data_access import load_prestasi
from components.filters import apply_filters, filter_summary_text, render_filters
from components.layout import format_number, missing_data_notice, page_header, section_title
from config.constants import CATEGORY_SHORT_LABELS
from modules.analytics import (
    category_summary,
    dosen_ranking,
    level_counts,
    peringkat_counts,
    student_ranking,
    summary_metrics,
)
from modules.date_helper import format_date_id
from modules.excel_export import build_report_excel
from modules.pdf_export import build_report_pdf


def _student_table(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(
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
    return frame.rename(
        columns={
            "ranking": "Peringkat",
            "nuptk": "NUPTK",
            "nama": "Nama Dosen",
            "jumlah_prestasi": "Jumlah Prestasi",
            "jumlah_mahasiswa": "Jumlah Mahasiswa",
            "juara1": "Juara 1",
            "juara2": "Juara 2",
            "juara3": "Juara 3",
            "poin": "Poin",
        }
    )


def _pdf_data_frame(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "Tanggal": format_date_id(row.get("tgl_sertifikat")),
                "NIM": row.get("mahasiswa_nim"),
                "Nama Mahasiswa": row.get("mahasiswa_nama"),
                "Kategori": CATEGORY_SHORT_LABELS.get(
                    row.get("kategori_kode"), row.get("kategori_nama") or row.get("kategori_kode")
                ),
                "Level": row.get("level_label"),
                "Lomba": row.get("lomba"),
                "Peringkat": row.get("peringkat_label"),
                "Dosen": row.get("dosen_nama"),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def _excel_bytes(frame: pd.DataFrame) -> bytes:
    return build_report_excel(frame)


@st.cache_data(show_spinner=False)
def _pdf_bytes(frame: pd.DataFrame, filter_text: str) -> bytes:
    metrics = summary_metrics(frame)
    summary_rows = [
        ("Total prestasi", format_number(metrics["total_prestasi"])),
        ("Mahasiswa berprestasi", format_number(metrics["total_mahasiswa"])),
        ("Dosen pendamping", format_number(metrics["total_dosen"])),
        ("Total kompetisi", format_number(metrics["total_kompetisi"])),
        ("Juara 1", format_number(metrics["juara1"])),
        ("Juara 2", format_number(metrics["juara2"])),
        ("Juara 3", format_number(metrics["juara3"])),
        ("Duplikat potensial", format_number(metrics["potensi_duplikat"])),
    ]
    sections = [
        {
            "title": "Rekap Kategori",
            "frame": category_summary(frame).rename(
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
        },
        {
            "title": "Sebaran Level",
            "frame": level_counts(frame).rename(
                columns={"level": "Kode", "level_label": "Level", "jumlah": "Jumlah Prestasi"}
            ),
        },
        {
            "title": "Sebaran Peringkat",
            "frame": peringkat_counts(frame).rename(
                columns={"peringkat": "Kode", "peringkat_label": "Peringkat", "jumlah": "Jumlah Prestasi"}
            ),
        },
        {
            "title": "Ranking Mahasiswa - 10 Besar",
            "frame": _student_table(student_ranking(frame).head(10)),
        },
        {
            "title": "Ranking Dosen - 10 Besar",
            "frame": _dosen_table(dosen_ranking(frame).head(10)),
        },
        {
            "title": "Lampiran Data Prestasi",
            "note": f"Menampilkan seluruh {format_number(len(frame))} baris prestasi pada data terfilter.",
            "frame": _pdf_data_frame(frame),
            "font_size": 6.5,
        },
    ]
    return build_report_pdf(
        title="Laporan Prestasi Mahasiswa",
        subtitle="Sistem Analisis Prestasi Mahasiswa (SAPM)",
        summary_rows=summary_rows,
        sections=sections,
        meta_lines=[f"Filter: {filter_text}", f"Jumlah baris: {format_number(len(frame))}"],
    )


def render() -> None:
    page_header(
        "Laporan",
        "Susun laporan prestasi terfilter dan unduh dalam format Excel atau PDF.",
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
                "subtitle": "NUPTK unik",
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

    preview_tab, download_tab = st.tabs(["Pratinjau Laporan", "Unduhan"])
    with preview_tab:
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

    with download_tab:
        section_title("Unduh Laporan")
        st.markdown(
            f"""
            <div class="sapm-note">
                Laporan akan mengikuti filter yang aktif: {filter_text}. File Excel memuat seluruh kolom data,
                sedangkan PDF memuat rekap, ranking, dan lampiran data ringkas.
            </div>
            """,
            unsafe_allow_html=True,
        )
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        left, right = st.columns(2)
        with left:
            st.download_button(
                "Unduh Laporan Excel",
                data=_excel_bytes(data),
                file_name=f"laporan_prestasi_{stamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        with right:
            st.download_button(
                "Unduh Laporan PDF",
                data=_pdf_bytes(data, filter_text),
                file_name=f"laporan_prestasi_{stamp}.pdf",
                mime="application/pdf",
                width="stretch",
            )
        st.caption("Pembuatan PDF dapat memerlukan beberapa detik untuk data berukuran besar.")
