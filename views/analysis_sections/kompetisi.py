from __future__ import annotations

from typing import List

import pandas as pd
import streamlit as st

from components.charts import donut_chart, ranking_bar_chart
from components.layout import format_number
from modules.analysis import kompetisi as analysis
from views.analysis_sections.shared import (
    chart_block,
    insight_block,
    metric_cards,
    ranking_table,
    section_header,
    table_block,
)

COMPETITION_LABELS = {
    "lomba": "Lomba",
    "tahun": "Tahun",
    "level": "Level",
    "kategori": "Kategori",
    "penyelenggara": "Penyelenggara",
    "cabang": "Cabang",
    "jumlah_prestasi": "Jumlah Prestasi",
    "jumlah_mahasiswa": "Mahasiswa",
}


def _insights(
    metrics: dict,
    level_summary: pd.DataFrame,
    organizers: pd.DataFrame,
    branches: pd.DataFrame,
    recurring: pd.DataFrame,
) -> List[str]:
    items = []
    if metrics["kompetisi_terbanyak"] != "-":
        items.append(
            f"Kompetisi dengan prestasi terbanyak adalah {metrics['kompetisi_terbanyak']} "
            f"dengan {format_number(metrics['prestasi_terbanyak'])} prestasi."
        )
    if not level_summary.empty:
        top = level_summary.iloc[0]
        items.append(
            f"Level dengan kompetisi terbanyak adalah {top['level_label']} dengan "
            f"{format_number(top['jumlah_kompetisi'])} edisi dan "
            f"{format_number(top['jumlah_lomba'])} judul lomba."
        )
    if not organizers.empty:
        top = organizers.iloc[0]
        items.append(
            f"Penyelenggara paling produktif adalah {top['penyelenggara']} dengan "
            f"{format_number(top['jumlah_prestasi'])} prestasi dari "
            f"{format_number(top['jumlah_kompetisi'])} edisi kompetisi."
        )
    if not branches.empty:
        top = branches.iloc[0]
        items.append(
            f"Cabang lomba terbanyak adalah {top['cabang']} dengan "
            f"{format_number(top['jumlah_prestasi'])} prestasi dan "
            f"{format_number(top['jumlah_mahasiswa'])} mahasiswa."
        )
    if not recurring.empty:
        top = recurring.iloc[0]
        if int(top["jumlah_edisi"]) > 1:
            items.append(
                f"Lomba yang berulang paling sering adalah {top['lomba']} dengan "
                f"{format_number(top['jumlah_edisi'])} edisi dari "
                f"{top['tahun_pertama']} sampai {top['tahun_terakhir']}."
            )
    return items


def render(frame: pd.DataFrame) -> None:
    metrics = analysis.metrics(frame)
    table = analysis.competition_table(frame)
    levels = analysis.level_summary(frame)
    organizers = analysis.organizer_summary(frame)
    branches = analysis.branch_summary(frame)
    recurring = analysis.recurring_competitions(frame)

    metric_cards(
        [
            {
                "title": "Edisi Kompetisi",
                "value": format_number(metrics["total_kompetisi"]),
                "subtitle": "Kombinasi lomba dan tahun",
                "color": "#2F80ED",
            },
            {
                "title": "Judul Lomba",
                "value": format_number(metrics["total_lomba"]),
                "subtitle": "Nama lomba unik",
                "color": "#1E4E8C",
            },
            {
                "title": "Penyelenggara",
                "value": format_number(metrics["total_penyelenggara"]),
                "subtitle": "Institusi unik",
                "color": "#1F9D55",
            },
            {
                "title": "Cabang Lomba",
                "value": format_number(metrics["total_cabang"]),
                "subtitle": "Bidang unik",
                "color": "#D97706",
            },
        ],
        columns=4,
    )

    section_header(
        "Kompetisi Terbanyak",
        "Peringkat edisi kompetisi berdasarkan jumlah prestasi dan mahasiswa.",
    )
    controls = st.columns([1, 2])
    with controls[0]:
        limit = st.selectbox(
            "Tampilkan",
            [10, 15, 25, 50],
            index=1,
            key="analysis_competition_limit",
        )
    with controls[1]:
        search = st.text_input(
            "Cari lomba, penyelenggara, atau cabang",
            key="analysis_competition_search",
            placeholder="Kata kunci",
        )
    filtered = table
    if search.strip():
        keyword = search.strip().lower()
        filtered = table[
            table["lomba"].fillna("").str.lower().str.contains(keyword, regex=False)
            | table["penyelenggara"].fillna("").str.lower().str.contains(keyword, regex=False)
            | table["cabang"].fillna("").str.lower().str.contains(keyword, regex=False)
        ]
    if filtered.empty:
        st.info("Tidak ada kompetisi yang sesuai pencarian.")
    else:
        chart_data = filtered.head(limit).copy()
        chart_data["label"] = chart_data["lomba"] + " (" + chart_data["tahun"] + ")"
        left, right = st.columns([1.15, 1])
        with left:
            chart_block(
                ranking_bar_chart(
                    chart_data,
                    label="label",
                    value="jumlah_prestasi",
                    top_n=limit,
                    height=440,
                ),
                caption="Edisi kompetisi dengan jumlah prestasi terbanyak.",
            )
        with right:
            section_header("Tabel Kompetisi", "Diurutkan berdasarkan jumlah prestasi.")
            ranking_table(filtered, COMPETITION_LABELS, height=440)

    left, right = st.columns(2)
    with left:
        section_header(
            "Komposisi Level Kompetisi",
            "Jumlah edisi kompetisi menurut level.",
        )
        chart_block(
            donut_chart(
                levels,
                names="level_label",
                values="jumlah_kompetisi",
                height=340,
                center_label="edisi",
                value_label="edisi",
            ),
            caption="Proporsi edisi kompetisi per level.",
        )
    with right:
        section_header(
            "Rekap Level",
            "Jumlah prestasi, edisi, judul lomba, dan mahasiswa per level.",
        )
        table_block(
            levels,
            labels={
                "level": "Kode",
                "level_label": "Level",
                "jumlah_prestasi": "Prestasi",
                "jumlah_kompetisi": "Edisi",
                "jumlah_lomba": "Judul Lomba",
                "jumlah_mahasiswa": "Mahasiswa",
            },
            height=340,
        )

    section_header(
        "Penyelenggara dan Cabang",
        "Institusi dan bidang lomba yang paling banyak menghasilkan prestasi.",
    )
    left, right = st.columns(2)
    with left:
        section_header("Penyelenggara Teratas", "Sepuluh penyelenggara dengan prestasi terbanyak.")
        if not organizers.empty:
            chart_block(
                ranking_bar_chart(
                    organizers.head(10).rename(columns={"penyelenggara": "label"}),
                    label="label",
                    value="jumlah_prestasi",
                    top_n=10,
                    height=360,
                    color="#1E4E8C",
                )
            )
            table_block(
                organizers.head(10),
                labels={
                    "penyelenggara": "Penyelenggara",
                    "jumlah_prestasi": "Prestasi",
                    "jumlah_kompetisi": "Edisi",
                    "jumlah_lomba": "Judul Lomba",
                    "jumlah_mahasiswa": "Mahasiswa",
                },
                height=300,
            )
        else:
            st.info("Data penyelenggara belum tersedia.")
    with right:
        section_header("Cabang Teratas", "Sepuluh cabang dengan prestasi terbanyak.")
        if not branches.empty:
            chart_block(
                ranking_bar_chart(
                    branches.head(10).rename(columns={"cabang": "label"}),
                    label="label",
                    value="jumlah_prestasi",
                    top_n=10,
                    height=360,
                    color="#1F9D55",
                )
            )
            table_block(
                branches.head(10),
                labels={
                    "cabang": "Cabang",
                    "jumlah_prestasi": "Prestasi",
                    "jumlah_kompetisi": "Edisi",
                    "jumlah_lomba": "Judul Lomba",
                    "jumlah_mahasiswa": "Mahasiswa",
                },
                height=300,
            )
        else:
            st.info("Data cabang belum tersedia.")

    section_header(
        "Kompetisi Berulang",
        "Lomba yang muncul pada lebih dari satu tahun, diurutkan berdasarkan jumlah edisi.",
    )
    table_block(
        recurring,
        labels={
            "lomba": "Lomba",
            "jumlah_edisi": "Jumlah Edisi",
            "jumlah_prestasi": "Jumlah Prestasi",
            "tahun_pertama": "Tahun Pertama",
            "tahun_terakhir": "Tahun Terakhir",
        },
        height=330,
        empty_message="Belum ada kompetisi yang tercatat pada lebih dari satu tahun.",
    )

    insight_block("Insight Kompetisi", _insights(metrics, levels, organizers, branches, recurring))
