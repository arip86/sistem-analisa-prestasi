from __future__ import annotations

from typing import List

import pandas as pd
import streamlit as st

from components.charts import bar_chart, donut_chart, heatmap_chart, line_chart
from components.layout import format_number
from modules.analysis import capaian
from modules.privacy import mask_nim
from views.analysis_sections.shared import (
    chart_block,
    insight_block,
    metric_cards,
    section_header,
    table_block,
)


def _insights(
    metrics: dict,
    category: pd.DataFrame,
    levels: pd.DataFrame,
    ranks: pd.DataFrame,
    yearly: pd.DataFrame,
    students_frame: pd.DataFrame,
) -> List[str]:
    items = []
    if not category.empty:
        top = category.iloc[0]
        items.append(
            f"Kategori terbanyak adalah {top['kategori']} dengan {format_number(top['jumlah_prestasi'])} prestasi "
            f"dari {format_number(top['mahasiswa_unik'])} mahasiswa."
        )
    if not levels.empty:
        top = levels.iloc[0]
        items.append(
            f"Level dominan adalah {top['level_label']} dengan {format_number(top['jumlah_prestasi'])} prestasi "
            f"dan {format_number(top['kompetisi_unik'])} kompetisi unik."
        )
    if not ranks.empty:
        top = ranks.iloc[0]
        items.append(
            f"Peringkat terbanyak adalah {top['peringkat_label']} sebanyak {format_number(top['jumlah_prestasi'])} prestasi."
        )
    if not yearly.empty:
        latest = yearly.sort_values("tahun").iloc[-1]
        items.append(
            f"Tahun terbaru pada data adalah {int(latest['tahun'])} dengan {format_number(latest['jumlah_prestasi'])} prestasi "
            f"dan {format_number(latest['mahasiswa_unik'])} mahasiswa."
        )
    if not students_frame.empty:
        top_student = students_frame.iloc[0]
        items.append(
            f"Mahasiswa dengan prestasi terbanyak adalah {top_student['nama']} "
            f"({mask_nim(top_student['nim'])}) dengan {format_number(top_student['jumlah_prestasi'])} "
            f"prestasi dan {format_number(top_student['poin'])} poin."
        )
    if metrics["total_kompetisi"]:
        items.append(
            f"Total cakupan data mencakup {format_number(metrics['total_kompetisi'])} edisi kompetisi "
            f"dari {metrics['tahun_awal'] or '-'} sampai {metrics['tahun_akhir'] or '-'}."
        )
    return items


def render(frame: pd.DataFrame) -> None:
    metrics = capaian.summary_metrics(frame)
    yearly = capaian.yearly_summary(frame)
    category = capaian.category_summary(frame)
    levels = capaian.level_summary(frame)
    ranks = capaian.rank_summary(frame)
    matrix = capaian.category_level_matrix(frame)
    yearly_level = capaian.level_yearly_matrix(frame)
    from modules.analysis.mahasiswa import ranking as student_ranking

    students = student_ranking(frame)
    average_year = (
        metrics["total_prestasi"] / metrics["jumlah_tahun"]
        if metrics["jumlah_tahun"]
        else 0
    )

    metric_cards(
        [
            {
                "title": "Total Prestasi",
                "value": format_number(metrics["total_prestasi"]),
                "subtitle": "Prestasi pada data terfilter",
                "color": "#2F80ED",
            },
            {
                "title": "Mahasiswa",
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
            {
                "title": "Total Poin",
                "value": format_number(metrics["total_poin"]),
                "subtitle": "Bobot level x bobot peringkat",
                "color": "#7C3AED",
            },
            {
                "title": "Rata-rata per Tahun",
                "value": f"{average_year:.1f}".replace(".", ","),
                "subtitle": f"{format_number(metrics['jumlah_tahun'])} tahun aktif",
                "color": "#0F766E",
            },
        ],
        columns=3,
    )

    section_header(
        "Capaian Utama",
        "Gambaran umum prestasi, sebaran kategori, level, peringkat, dan hubungan antar-dimensi.",
    )
    left, right = st.columns([1.25, 1])
    with left:
        if not yearly.empty:
            chart_block(
                line_chart(
                    yearly,
                    x="tahun",
                    y="jumlah_prestasi",
                    text="jumlah_prestasi",
                    height=360,
                ),
                caption="Jumlah prestasi per tahun berdasarkan tanggal sertifikat.",
            )
        else:
            st.info("Data tahunan belum tersedia.")
    with right:
        if not category.empty:
            chart_block(
                donut_chart(
                    category,
                    names="kategori",
                    values="jumlah_prestasi",
                    height=360,
                ),
                caption="Komposisi prestasi per kategori.",
            )
        else:
            st.info("Sebaran kategori belum tersedia.")

    left, right = st.columns(2)
    with left:
        if not levels.empty:
            chart_block(
                bar_chart(
                    levels,
                    x="level_label",
                    y="jumlah_prestasi",
                    text="jumlah_prestasi",
                    height=340,
                ),
                caption="Jumlah prestasi menurut level kompetisi.",
            )
    with right:
        if not ranks.empty:
            chart_block(
                bar_chart(
                    ranks,
                    x="peringkat_label",
                    y="jumlah_prestasi",
                    text="jumlah_prestasi",
                    height=340,
                ),
                caption="Jumlah prestasi menurut peringkat.",
            )

    section_header(
        "Matriks Kategori dan Level",
        "Semakin gelap warna sel, semakin banyak prestasi pada kombinasi tersebut.",
    )
    if not matrix.empty:
        chart_block(
            heatmap_chart(
                matrix,
                x="level_label",
                y="kategori",
                values="jumlah_prestasi",
                height=340,
            ),
            caption="Sebaran prestasi per kategori dan level kompetisi.",
        )
    else:
        st.info("Matriks kategori dan level belum tersedia.")

    if not yearly_level.empty:
        with st.expander("Lihat tren level per tahun", expanded=False):
            chart_block(
                bar_chart(
                    yearly_level,
                    x="tahun",
                    y="jumlah_prestasi",
                    color="level_label",
                    height=360,
                ),
                caption="Komposisi level kompetisi dari tahun ke tahun.",
            )

    section_header("Rekap Kategori", "Ringkasan jumlah prestasi, mahasiswa, kompetisi, dan poin.")
    table_block(
        category,
        labels={
            "kategori_kode": "Kode",
            "kategori": "Kategori",
            "jumlah_prestasi": "Jumlah Prestasi",
            "mahasiswa_unik": "Mahasiswa Unik",
            "kompetisi_unik": "Kompetisi Unik",
            "level_unik": "Level Unik",
            "poin": "Poin",
        },
        empty_message="Rekap kategori belum tersedia.",
    )

    section_header("Rekap Level", "Ringkasan jumlah prestasi, mahasiswa, kompetisi, dan poin per level.")
    table_block(
        levels,
        labels={
            "level": "Kode",
            "level_label": "Level",
            "jumlah_prestasi": "Jumlah Prestasi",
            "mahasiswa_unik": "Mahasiswa Unik",
            "kompetisi_unik": "Kompetisi Unik",
            "poin": "Poin",
        },
        empty_message="Rekap level belum tersedia.",
    )

    insight_block(
        "Insight Otomatis",
        _insights(metrics, category, levels, ranks, yearly, students),
    )
    st.markdown(
        """
        <div class="sapm-note">
            Metodologi poin: level Internasional 5, Nasional 3, Provinsi 2, Kabupaten/Kota 1.
            Peringkat Juara 1 = 3, Juara 2 = 2, Juara 3 = 1, Harapan = 1.
            Kompetisi unik dihitung dari kombinasi nama lomba dan tahun.
        </div>
        """,
        unsafe_allow_html=True,
    )
