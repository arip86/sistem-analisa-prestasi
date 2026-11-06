from __future__ import annotations

from typing import List

import pandas as pd
import streamlit as st

from components.charts import bar_chart, ranking_bar_chart
from components.layout import format_number
from modules.analysis import dosen as analysis
from views.analysis_sections.shared import (
    chart_block,
    insight_block,
    metric_cards,
    ranking_table,
    section_header,
    table_block,
)

RANK_LABELS = {
    "ranking": "Peringkat",
    "nuptk": "NUPTK",
    "nama": "Nama Dosen",
    "jumlah_prestasi": "Jumlah Prestasi",
    "jumlah_mahasiswa": "Jumlah Mahasiswa",
    "poin": "Poin",
    "jumlah_kategori": "Kategori",
    "jumlah_level": "Level",
    "juara1": "Juara 1",
    "juara2": "Juara 2",
    "juara3": "Juara 3",
    "periode_pertama": "Periode Awal",
    "periode_terakhir": "Periode Akhir",
}


def _insights(metrics: dict, ranking: pd.DataFrame, student_distribution: pd.DataFrame) -> List[str]:
    items = []
    if not ranking.empty:
        top = ranking.iloc[0]
        items.append(
            f"Dosen dengan prestasi terbanyak adalah {top['nama']} dengan "
            f"{format_number(top['jumlah_prestasi'])} prestasi dan "
            f"{format_number(top['jumlah_mahasiswa'])} mahasiswa."
        )
        most_students = ranking.sort_values(
            ["jumlah_mahasiswa", "jumlah_prestasi", "nama"],
            ascending=[False, False, True],
        ).iloc[0]
        items.append(
            f"Dosen yang mendampingi mahasiswa terbanyak adalah {most_students['nama']} "
            f"dengan {format_number(most_students['jumlah_mahasiswa'])} mahasiswa."
        )
    items.append(
        f"Rata-rata seorang dosen mendampingi {metrics['rata_mahasiswa']:.1f} mahasiswa.".replace(".", ",")
    )
    if metrics["dosen_multiple"]:
        items.append(
            f"Sebanyak {format_number(metrics['dosen_multiple'])} dosen memiliki lebih dari satu prestasi."
        )
    if not student_distribution.empty:
        single = student_distribution[student_distribution["jumlah_mahasiswa"] == 1]
        if not single.empty:
            items.append(
                f"Sebanyak {format_number(single.iloc[0]['jumlah_dosen'])} dosen mendampingi satu mahasiswa."
            )
    return items


def render(frame: pd.DataFrame) -> None:
    metrics = analysis.metrics(frame)
    ranking = analysis.ranking(frame)
    student_distribution = analysis.student_distribution(frame)
    level_distribution = analysis.distribution(frame, dimension="level_label", top_n=10)
    category_distribution = analysis.distribution(frame, dimension="kategori_nama", top_n=10)

    metric_cards(
        [
            {
                "title": "Dosen Pendamping",
                "value": format_number(metrics["total_dosen"]),
                "subtitle": "NUPTK unik setelah relasi",
                "color": "#1E4E8C",
            },
            {
                "title": "Rata-rata Mahasiswa",
                "value": f"{metrics['rata_mahasiswa']:.1f}".replace(".", ","),
                "subtitle": "Mahasiswa per dosen",
                "color": "#2F80ED",
            },
            {
                "title": "Dosen dengan Prestasi Berulang",
                "value": format_number(metrics["dosen_multiple"]),
                "subtitle": "Lebih dari satu prestasi",
                "color": "#1F9D55",
            },
            {
                "title": "Mahasiswa Terbanyak",
                "value": format_number(metrics["mahasiswa_terbanyak"]),
                "subtitle": "Jumlah mahasiswa pada satu dosen",
                "color": "#D97706",
            },
        ],
        columns=4,
    )

    section_header(
        "Peringkat Dosen Pendamping",
        "Peringkat utama berdasarkan jumlah prestasi, dilengkapi jumlah mahasiswa dan poin.",
    )
    controls = st.columns([1.2, 1, 1])
    with controls[0]:
        metric_label = st.radio(
            "Indikator peringkat",
            ["Jumlah prestasi", "Poin", "Jumlah mahasiswa"],
            horizontal=True,
            key="analysis_lecturer_metric",
        )
    with controls[1]:
        limit = st.selectbox(
            "Tampilkan",
            [10, 15, 25, 50],
            index=1,
            key="analysis_lecturer_limit",
        )
    with controls[2]:
        search = st.text_input(
            "Cari nama atau NUPTK",
            key="analysis_lecturer_search",
            placeholder="Kata kunci",
        )

    value_column = {
        "Jumlah prestasi": "jumlah_prestasi",
        "Poin": "poin",
        "Jumlah mahasiswa": "jumlah_mahasiswa",
    }[metric_label]
    filtered = ranking
    if search.strip():
        keyword = search.strip().lower()
        filtered = ranking[
            ranking["nama"].fillna("").str.lower().str.contains(keyword, regex=False)
            | ranking["nuptk"].fillna("").astype(str).str.contains(keyword, regex=False)
        ]
    if filtered.empty:
        st.info("Tidak ada dosen yang sesuai pencarian.")
    else:
        chart_data = filtered.head(limit).copy()
        chart_data["label"] = chart_data["nama"] + " (" + chart_data["nuptk"] + ")"
        left, right = st.columns([1.15, 1])
        with left:
            chart_block(
                ranking_bar_chart(
                    chart_data,
                    label="label",
                    value=value_column,
                    top_n=limit,
                    height=450,
                    color="#1E4E8C",
                ),
                caption=f"Peringkat dosen berdasarkan {metric_label.lower()}.",
            )
        with right:
            section_header("Tabel Peringkat", f"Diurutkan berdasarkan {metric_label.lower()}.")
            display = filtered.sort_values(
                [value_column, "jumlah_prestasi", "jumlah_mahasiswa", "nama"],
                ascending=[False, False, False, True],
            ).copy()
            display = display.reset_index(drop=True)
            display["ranking"] = range(1, len(display) + 1)
            ranking_table(display, RANK_LABELS, height=450)

    left, right = st.columns(2)
    with left:
        section_header(
            "Sebaran Level yang Didampingi",
            "Sepuluh dosen dengan prestasi terbanyak, dirinci menurut level.",
        )
        if not level_distribution.empty:
            chart_block(
                bar_chart(
                    level_distribution,
                    x="dosen_label",
                    y="jumlah_prestasi",
                    color="level_label",
                    orientation="h",
                    height=390,
                ),
                caption="Komposisi level prestasi pada dosen dengan capaian terbanyak.",
            )
        else:
            st.info("Sebaran level dosen belum tersedia.")
    with right:
        section_header(
            "Sebaran Kategori yang Didampingi",
            "Sepuluh dosen dengan prestasi terbanyak, dirinci menurut kategori.",
        )
        if not category_distribution.empty:
            chart_block(
                bar_chart(
                    category_distribution,
                    x="dosen_label",
                    y="jumlah_prestasi",
                    color="kategori_nama",
                    orientation="h",
                    height=390,
                ),
                caption="Komposisi kategori prestasi pada dosen dengan capaian terbanyak.",
            )
        else:
            st.info("Sebaran kategori dosen belum tersedia.")

    section_header(
        "Distribusi Jumlah Mahasiswa",
        "Berapa banyak dosen yang mendampingi 1, 2, 3, dan seterusnya mahasiswa.",
    )
    chart_block(
        bar_chart(
            student_distribution,
            x="jumlah_mahasiswa",
            y="jumlah_dosen",
            text="jumlah_dosen",
            height=320,
        )
    )

    insight_block("Insight Dosen", _insights(metrics, ranking, student_distribution))
