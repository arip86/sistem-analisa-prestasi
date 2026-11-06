from __future__ import annotations

from typing import Tuple

import pandas as pd
import streamlit as st

from components.charts import bar_chart, line_chart, multi_line_chart
from components.layout import format_number
from modules.analysis import tren
from views.analysis_sections.shared import (
    chart_block,
    metric_cards,
    percentage_text,
    section_header,
    show_no_data,
    table_block,
)

METRIC_OPTIONS = {
    "Jumlah prestasi": "jumlah_prestasi",
    "Mahasiswa aktif": "mahasiswa_unik",
    "Kompetisi": "kompetisi_unik",
}


def _select_periods(periods: list[str]) -> Tuple[str, str]:
    if not periods:
        return "", ""
    if len(periods) == 1:
        return periods[0], periods[0]
    return periods[-2], periods[-1]


def _comparison_cards(first: str, second: str, comparison: dict) -> None:
    change = comparison["persentase"]
    metric_cards(
        [
            {
                "title": f"Periode {first}",
                "value": format_number(comparison["jumlah_pertama"]),
                "subtitle": f"{format_number(comparison['mahasiswa_pertama'])} mahasiswa aktif",
                "color": "#1E4E8C",
            },
            {
                "title": f"Periode {second}",
                "value": format_number(comparison["jumlah_kedua"]),
                "subtitle": f"{format_number(comparison['mahasiswa_kedua'])} mahasiswa aktif",
                "color": "#2F80ED",
            },
            {
                "title": "Perubahan",
                "value": percentage_text(change),
                "subtitle": (
                    f"Selisih +{format_number(comparison['selisih'])} prestasi"
                    if comparison["selisih"] > 0
                    else f"Selisih {format_number(comparison['selisih'])} prestasi"
                ),
                "color": "#1F9D55" if (change or 0) >= 0 else "#C0392B",
            },
        ],
        columns=3,
    )


def render(frame: pd.DataFrame) -> None:
    st.markdown(
        '<div class="sapm-control-label">Pilih resolusi waktu dan indikator yang ingin dianalisis.</div>',
        unsafe_allow_html=True,
    )
    controls = st.columns([1, 1.4])
    with controls[0]:
        granularity = st.radio(
            "Resolusi waktu",
            ["Tahunan", "Bulanan"],
            horizontal=True,
            key="analysis_tren_granularity",
        )
    with controls[1]:
        metric_label = st.radio(
            "Indikator",
            list(METRIC_OPTIONS),
            horizontal=True,
            key="analysis_tren_metric",
        )
    metric = METRIC_OPTIONS[metric_label]

    summary = tren.period_summary(frame, granularity)
    if summary.empty:
        show_no_data("Tren waktu belum tersedia untuk data terfilter.")
        return

    metrics = tren.trend_metrics(frame, granularity)
    metric_cards(
        [
            {
                "title": "Periode Tercatat",
                "value": format_number(metrics["periode"]),
                "subtitle": f"{metrics['periode_pertama']} sampai {metrics['periode_terakhir']}",
                "color": "#1E4E8C",
            },
            {
                "title": "Puncak Prestasi",
                "value": metrics["puncak"],
                "subtitle": f"{format_number(metrics['prestasi_puncak'])} prestasi",
                "color": "#2F80ED",
            },
            {
                "title": "Rata-rata per Periode",
                "value": f"{metrics['rata_rata']:.1f}".replace(".", ","),
                "subtitle": "Prestasi per periode",
                "color": "#1F9D55",
            },
            {
                "title": "Pertumbuhan Awal-Akhir",
                "value": percentage_text(metrics["pertumbuhan"]),
                "subtitle": "Perubahan periode terakhir dibanding pertama",
                "color": "#D97706" if (metrics["pertumbuhan"] or 0) >= 0 else "#C0392B",
            },
        ],
        columns=4,
    )

    section_header(
        f"Tren {metric_label} per {granularity[:-2] if granularity == 'Tahunan' else 'Bulan'}",
        "Arah dan besaran perubahan capaian dari waktu ke waktu.",
    )
    chart_block(
        line_chart(
            summary,
            x="periode",
            y=metric,
            text=metric,
            height=370,
        ),
        caption="Periode tanpa data ditampilkan sebagai nol agar arah tren tetap terbaca.",
    )

    section_header(
        "Perbandingan Dua Periode",
        "Bandingkan jumlah prestasi dan mahasiswa aktif pada dua periode yang dipilih.",
    )
    periods = summary["periode"].tolist()
    first_default, second_default = _select_periods(periods)
    compare_left, compare_right = st.columns(2)
    with compare_left:
        first = st.selectbox(
            "Periode pembanding",
            periods,
            index=periods.index(first_default),
            key="analysis_tren_period_a",
        )
    with compare_right:
        second = st.selectbox(
            "Periode utama",
            periods,
            index=periods.index(second_default),
            key="analysis_tren_period_b",
        )
    comparison = tren.period_comparison(frame, granularity, first, second)
    _comparison_cards(first, second, comparison)

    section_header(
        "Pola Musiman per Tahun",
        "Bulan yang sama dibandingkan antar-tahun untuk melihat pola musiman.",
    )
    monthly = tren.monthly_by_year(frame)
    if not monthly.empty:
        chart_block(
            multi_line_chart(
                monthly,
                x="bulan_label",
                y="jumlah_prestasi",
                color="tahun",
                height=390,
            ),
            caption="Setiap garis mewakili satu tahun. Bulan disusun dari Januari sampai Desember.",
        )
    else:
        st.info("Pola musiman belum tersedia karena tanggal sertifikat tidak lengkap.")

    left, right = st.columns([1.1, 1])
    with left:
        section_header("Jumlah per Periode", "Perbandingan langsung antar-periode.")
        chart_block(
            bar_chart(
                summary,
                x="periode",
                y=metric,
                text=metric,
                height=330,
            )
        )
    with right:
        section_header("Tabel Pertumbuhan", "Selisih dan persentase perubahan dari periode sebelumnya.")
        table_block(
            summary,
            labels={
                "periode": "Periode",
                "jumlah_prestasi": "Prestasi",
                "mahasiswa_unik": "Mahasiswa",
                "kompetisi_unik": "Kompetisi",
                "selisih": "Selisih",
                "persentase": "Perubahan (%)",
            },
            height=330,
            empty_message="Tabel pertumbuhan belum tersedia.",
        )

    fastest = summary.dropna(subset=["persentase"])
    if not fastest.empty:
        top = fastest.sort_values("persentase", ascending=False).iloc[0]
        lowest = fastest.sort_values("persentase", ascending=True).iloc[0]
        st.markdown(
            f"""
            <div class="sapm-note">
                Pertumbuhan tertinggi terjadi pada periode <b>{top['periode']}</b>
                sebesar <b>{percentage_text(top['persentase'])}</b>.
                Pertumbuhan terendah terjadi pada periode <b>{lowest['periode']}</b>
                sebesar <b>{percentage_text(lowest['persentase'])}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )
