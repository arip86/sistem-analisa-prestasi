from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from components.cards import render_highlight_grid, render_kpi_grid
from components.charts import bar_chart, donut_chart, line_chart, ranking_bar_chart
from components.data_access import load_prestasi
from components.filters import apply_filters, filter_summary_text, render_filters
from components.layout import format_number, missing_data_notice, page_header, section_title
from modules.analytics import (
    category_counts,
    dosen_ranking,
    level_counts,
    peringkat_counts,
    student_ranking,
    summary_metrics,
)
from modules.date_helper import format_date_id
from modules.privacy import mask_nim


def _recent_frame(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy().sort_values("tgl_sertifikat", ascending=False).head(8)
    return pd.DataFrame(
        [
            {
                "Tanggal": format_date_id(row.get("tgl_sertifikat")),
                "NIM": mask_nim(row.get("mahasiswa_nim")),
                "Nama Mahasiswa": row.get("mahasiswa_nama"),
                "Lomba": row.get("lomba"),
                "Level": row.get("level_label"),
                "Peringkat": row.get("peringkat_label"),
                "Dosen": row.get("dosen_nama"),
            }
            for _, row in data.iterrows()
        ]
    )


def _monthly_frame(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.dropna(subset=["tgl_sertifikat"]).copy()
    if data.empty:
        return pd.DataFrame(columns=["periode", "jumlah"])
    data["periode"] = data["tgl_sertifikat"].dt.strftime("%Y-%m")
    return (
        data.groupby("periode", as_index=False)
        .size()
        .rename(columns={"size": "jumlah"})
        .sort_values("periode")
    )


def render() -> None:
    page_header(
        "Dasbor Prestasi Mahasiswa",
        "Ringkasan capaian, sebaran, tren, dan sorotan utama prestasi mahasiswa.",
    )
    frame, error = load_prestasi()
    if error:
        st.error(f"Data belum dapat dimuat: {error}")
        return
    if frame.empty:
        missing_data_notice()
        return

    filters = render_filters(frame, "dashboard", expanded=False, columns=3)
    data = apply_filters(frame, filters)
    st.caption(
        f"Menampilkan {format_number(len(data))} dari {format_number(len(frame))} prestasi. "
        f"Filter: {filter_summary_text(filters)}"
    )
    if data.empty:
        st.warning("Tidak ada prestasi yang sesuai dengan filter.")
        return

    metrics = summary_metrics(data)
    categories = category_counts(data)
    levels = level_counts(data)
    ranks = peringkat_counts(data)
    students = student_ranking(data)
    lecturers = dosen_ranking(data)

    render_kpi_grid(
        [
            {
                "title": "Total Prestasi",
                "value": format_number(metrics["total_prestasi"]),
                "subtitle": "Baris prestasi pada data terfilter",
                "color": "#2F80ED",
            },
            {
                "title": "Mahasiswa Berprestasi",
                "value": format_number(metrics["total_mahasiswa"]),
                "subtitle": "NIM unik setelah relasi",
                "color": "#1E4E8C",
            },
            {
                "title": "Dosen Pendamping",
                "value": format_number(metrics["total_dosen"]),
                "subtitle": "Dosen unik setelah relasi",
                "color": "#1F9D55",
            },
            {
                "title": "Kompetisi",
                "value": format_number(metrics["total_kompetisi"]),
                "subtitle": "Kombinasi lomba dan tahun",
                "color": "#D97706",
            },
        ]
    )

    top_category = categories.iloc[0] if not categories.empty else None
    top_level = levels.iloc[0] if not levels.empty else None
    top_student = students.iloc[0] if not students.empty else None
    top_lecturer = lecturers.iloc[0] if not lecturers.empty else None
    render_highlight_grid(
        [
            {
                "label": "Mahasiswa Teratas",
                "value": top_student["nama"] if top_student is not None else "-",
                "meta": (
                    f"{format_number(top_student['jumlah_prestasi'])} prestasi | "
                    f"{format_number(top_student['poin'])} poin"
                    if top_student is not None
                    else "Belum ada data"
                ),
                "color": "#2F80ED",
            },
            {
                "label": "Dosen Teratas",
                "value": top_lecturer["nama"] if top_lecturer is not None else "-",
                "meta": (
                    f"{format_number(top_lecturer['jumlah_prestasi'])} prestasi | "
                    f"{format_number(top_lecturer['jumlah_mahasiswa'])} mahasiswa"
                    if top_lecturer is not None
                    else "Belum ada data"
                ),
                "color": "#1E4E8C",
            },
            {
                "label": "Kategori Teratas",
                "value": top_category["kategori"] if top_category is not None else "-",
                "meta": (
                    f"{format_number(top_category['jumlah'])} prestasi"
                    if top_category is not None
                    else "Belum ada data"
                ),
                "color": "#1F9D55",
            },
            {
                "label": "Level Teratas",
                "value": top_level["level_label"] if top_level is not None else "-",
                "meta": (
                    f"{format_number(top_level['jumlah'])} prestasi"
                    if top_level is not None
                    else "Belum ada data"
                ),
                "color": "#D97706",
            },
        ]
    )

    monthly = _monthly_frame(data)
    with st.container(border=True):
        left, right = st.columns([1.3, 1])
        with left:
            section_title("Tren Prestasi per Bulan", "Berdasarkan tanggal sertifikat")
            st.plotly_chart(
                line_chart(monthly, x="periode", y="jumlah", height=350),
                width="stretch",
            )
        with right:
            section_title("Peringkat Mahasiswa", "Berdasarkan poin berbobot level dan peringkat")
            if students.empty:
                st.info("Belum ada data peringkat.")
            else:
                chart_data = students.rename(columns={"nama": "Nama", "poin": "Poin"}).head(10)
                st.plotly_chart(
                    ranking_bar_chart(
                        chart_data,
                        label="Nama",
                        value="Poin",
                        top_n=10,
                        height=350,
                    ),
                    width="stretch",
                )

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            section_title("Sebaran Kategori", "Komposisi prestasi per kategori")
            st.plotly_chart(
                donut_chart(
                    categories,
                    names="kategori",
                    values="jumlah",
                    height=350,
                ),
                width="stretch",
            )
    with right:
        with st.container(border=True):
            section_title("Sebaran Level", "Jumlah prestasi menurut tingkat kompetisi")
            st.plotly_chart(
                bar_chart(
                    levels,
                    x="level_label",
                    y="jumlah",
                    text="jumlah",
                    height=350,
                ),
                width="stretch",
            )

    with st.container(border=True):
        section_title(
            "Sebaran Peringkat",
            "Komposisi juara dan harapan pada data terfilter",
        )
        st.plotly_chart(
            bar_chart(
                ranks,
                x="peringkat_label",
                y="jumlah",
                text="jumlah",
                height=310,
            ),
            width="stretch",
        )

    with st.container(border=True):
        section_title("Prestasi Terbaru", "Delapan prestasi dengan tanggal sertifikat terbaru")
        st.dataframe(
            _recent_frame(data),
            width="stretch",
            hide_index=True,
            height=330,
        )

    summary_lines = []
    if top_student is not None:
        summary_lines.append(
            f"{html.escape(str(top_student['nama']))} memimpin dengan "
            f"{format_number(top_student['jumlah_prestasi'])} prestasi dan {format_number(top_student['poin'])} poin."
        )
    if top_category is not None:
        summary_lines.append(
            f"Kategori {html.escape(str(top_category['kategori']))} menjadi kontributor utama "
            f"dengan {format_number(top_category['jumlah'])} prestasi."
        )
    if top_level is not None:
        summary_lines.append(
            f"Level {html.escape(str(top_level['level_label']))} mendominasi dengan "
            f"{format_number(top_level['jumlah'])} prestasi."
        )
    if metrics["potensi_duplikat"]:
        summary_lines.append(
            f"Terdapat {format_number(metrics['potensi_duplikat'])} baris duplikat potensial yang perlu diverifikasi."
        )
    if summary_lines:
        st.markdown(
            f"""
            <div class="sapm-note">
                <b>Ringkasan cepat.</b> {' '.join(summary_lines)}
            </div>
            """,
            unsafe_allow_html=True,
        )
