from __future__ import annotations

from typing import List

import pandas as pd
import streamlit as st

from components.charts import bar_chart, donut_chart, ranking_bar_chart
from components.layout import format_number
from modules.analysis import mahasiswa as analysis
from modules.privacy import mask_nim, mask_nim_column
from views.analysis_sections.shared import (
    chart_block,
    insight_block,
    metric_cards,
    ranking_table,
    ratio_text,
    section_header,
    table_block,
)

RANK_LABELS = {
    "ranking": "Peringkat",
    "nim": "NIM",
    "nama": "Nama Mahasiswa",
    "jumlah_prestasi": "Jumlah Prestasi",
    "poin": "Poin",
    "jumlah_kategori": "Kategori",
    "jumlah_level": "Level",
    "juara1": "Juara 1",
    "juara2": "Juara 2",
    "juara3": "Juara 3",
    "periode_pertama": "Periode Awal",
    "periode_terakhir": "Periode Akhir",
}

CONSISTENCY_LABELS = {
    "nim": "NIM",
    "nama": "Nama Mahasiswa",
    "jumlah_prestasi": "Jumlah Prestasi",
    "tahun_aktif": "Tahun Aktif",
    "bulan_aktif": "Bulan Aktif",
    "rentang_bulan": "Rentang Bulan",
    "rasio_konsistensi": "Rasio Konsistensi",
    "periode_pertama": "Periode Awal",
    "periode_terakhir": "Periode Akhir",
}


def _insights(
    metrics: dict,
    ranking: pd.DataFrame,
    consistency: pd.DataFrame,
    distribution: pd.DataFrame,
) -> List[str]:
    items = []
    if not ranking.empty:
        top = ranking.iloc[0]
        items.append(
            f"Mahasiswa dengan prestasi terbanyak adalah {top['nama']} ({mask_nim(top['nim'])}) "
            f"dengan {format_number(top['jumlah_prestasi'])} prestasi dan {format_number(top['poin'])} poin."
        )
    if metrics["mahasiswa_multiple"]:
        share = metrics["mahasiswa_multiple"] / metrics["total_mahasiswa"] * 100
        items.append(
            f"Sebanyak {format_number(metrics['mahasiswa_multiple'])} mahasiswa memiliki lebih dari satu prestasi "
            f"({share:.1f}% dari mahasiswa berprestasi).".replace(".", ",")
        )
    if not consistency.empty:
        top_consistent = consistency.iloc[0]
        items.append(
            f"Rasio konsistensi tertinggi adalah {top_consistent['nama']} dengan nilai "
            f"{ratio_text(top_consistent['rasio_konsistensi'])} dari "
            f"{format_number(top_consistent['bulan_aktif'])} bulan aktif dalam "
            f"{format_number(top_consistent['rentang_bulan'])} bulan."
        )
    if not distribution.empty:
        single = distribution[distribution["jumlah_prestasi"] == 1]
        if not single.empty:
            items.append(
                f"Sebanyak {format_number(single.iloc[0]['jumlah_mahasiswa'])} mahasiswa baru memiliki satu prestasi."
            )
    items.append(
        f"Prestasi individu tercatat {format_number(metrics['prestasi_individu'])} dan prestasi kelompok "
        f"{format_number(metrics['prestasi_kelompok'])}."
    )
    if metrics["mahasiswa_internasional"] == 0:
        items.append("Tidak ada mahasiswa dengan prestasi internasional pada data terfilter.")
    return items


def render(frame: pd.DataFrame) -> None:
    metrics = analysis.metrics(frame)
    ranking = analysis.ranking(frame)
    consistency = analysis.consistency(frame)
    distribution = analysis.distribution(frame)
    groups = analysis.group_distribution(frame)
    international = analysis.international(frame)

    metric_cards(
        [
            {
                "title": "Mahasiswa Berprestasi",
                "value": format_number(metrics["total_mahasiswa"]),
                "subtitle": "NIM unik setelah relasi",
                "color": "#2F80ED",
            },
            {
                "title": "Lebih dari Satu Prestasi",
                "value": format_number(metrics["mahasiswa_multiple"]),
                "subtitle": "Mahasiswa dengan prestasi berulang",
                "color": "#1F9D55",
            },
            {
                "title": "Prestasi Individu",
                "value": format_number(metrics["prestasi_individu"]),
                "subtitle": "Kelompok prestasi INDIVIDU",
                "color": "#1E4E8C",
            },
            {
                "title": "Prestasi Kelompok",
                "value": format_number(metrics["prestasi_kelompok"]),
                "subtitle": "Kelompok prestasi KELOMPOK",
                "color": "#D97706",
            },
        ],
        columns=4,
    )

    section_header(
        "Peringkat Mahasiswa",
        "Peringkat utama berdasarkan jumlah prestasi. Peringkat poin tetap tersedia melalui pilihan indikator.",
    )
    controls = st.columns([1.2, 1, 1])
    with controls[0]:
        metric_label = st.radio(
            "Indikator peringkat",
            ["Jumlah prestasi", "Poin"],
            horizontal=True,
            key="analysis_student_metric",
        )
    with controls[1]:
        limit = st.selectbox(
            "Tampilkan",
            [10, 15, 25, 50],
            index=1,
            key="analysis_student_limit",
        )
    with controls[2]:
        search = st.text_input(
            "Cari nama atau NIM",
            key="analysis_student_search",
            placeholder="Kata kunci",
        )
    value_column = "poin" if metric_label == "Poin" else "jumlah_prestasi"
    display_ranking = mask_nim_column(ranking)
    filtered = display_ranking
    if search.strip():
        keyword = search.strip().lower()
        filtered = display_ranking[
            display_ranking["nama"].fillna("").str.lower().str.contains(keyword, regex=False)
            | display_ranking["nim"].fillna("").astype(str).str.contains(keyword, regex=False)
        ]
    if filtered.empty:
        st.info("Tidak ada mahasiswa yang sesuai pencarian.")
    else:
        chart_data = filtered.head(limit).copy()
        chart_data["label"] = chart_data["nama"] + " (" + chart_data["nim"] + ")"
        left, right = st.columns([1.15, 1])
        with left:
            chart_block(
                ranking_bar_chart(
                    chart_data,
                    label="label",
                    value=value_column,
                    top_n=limit,
                    height=430,
                ),
                caption=f"Peringkat mahasiswa berdasarkan {metric_label.lower()}.",
            )
        with right:
            section_header("Tabel Peringkat", f"Diurutkan berdasarkan {metric_label.lower()}.")
            display = filtered.sort_values(
                [value_column, "poin", "nama"] if value_column == "poin" else ["jumlah_prestasi", "poin", "nama"],
                ascending=[False, False, True],
            ).copy()
            display = display.reset_index(drop=True)
            display["ranking"] = range(1, len(display) + 1)
            ranking_table(display, RANK_LABELS, height=430)

    section_header(
        "Konsistensi Mahasiswa",
        "Rasio = jumlah bulan aktif / rentang bulan dari prestasi pertama sampai terakhir.",
    )
    minimum = st.selectbox(
        "Minimal jumlah prestasi",
        [1, 2, 3, 4],
        index=1,
        key="analysis_student_consistency_min",
    )
    consistent = consistency[consistency["jumlah_prestasi"] >= minimum]
    consistent_display = mask_nim_column(consistent)
    table_block(
        consistent_display,
        labels=CONSISTENCY_LABELS,
        height=360,
        empty_message="Belum ada mahasiswa yang memenuhi kriteria konsistensi.",
    )
    if not consistent.empty:
        top_consistent = mask_nim_column(consistent.head(10))
        top_consistent["label"] = top_consistent["nama"] + " (" + top_consistent["nim"] + ")"
        chart_block(
            bar_chart(
                top_consistent.sort_values("rasio_konsistensi", ascending=True),
                x="label",
                y="rasio_konsistensi",
                orientation="h",
                text="rasio_konsistensi",
                height=360,
            ),
            caption="Sepuluh mahasiswa dengan rasio konsistensi tertinggi pada kriteria terpilih.",
        )

    left, right = st.columns(2)
    with left:
        section_header(
            "Sebaran Jumlah Prestasi",
            "Berapa banyak mahasiswa yang memiliki 1, 2, 3, dan seterusnya prestasi.",
        )
        chart_block(
            bar_chart(
                distribution,
                x="jumlah_prestasi",
                y="jumlah_mahasiswa",
                text="jumlah_mahasiswa",
                height=330,
            )
        )
    with right:
        section_header(
            "Komposisi Individu dan Kelompok",
            "Berdasarkan field kelompok prestasi.",
        )
        chart_block(
            donut_chart(
                groups,
                names="kelompok",
                values="jumlah_prestasi",
                height=330,
                center_label="prestasi",
            )
        )

    section_header(
        "Prestasi Internasional",
        "Daftar mahasiswa dengan prestasi pada level internasional.",
    )
    table_block(
        mask_nim_column(international),
        labels={
            "nim": "NIM",
            "nama": "Nama Mahasiswa",
            "jumlah_prestasi": "Jumlah Prestasi",
            "lomba": "Lomba",
            "peringkat": "Peringkat",
            "tahun": "Tahun",
            "dosen": "Dosen Pendamping",
        },
        height=300,
        empty_message="Tidak ada prestasi internasional pada data terfilter.",
    )

    insight_block("Insight Mahasiswa", _insights(metrics, ranking, consistency, distribution))
