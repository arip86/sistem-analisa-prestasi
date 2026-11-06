from __future__ import annotations

from typing import List

import pandas as pd
import streamlit as st

from components.charts import bar_chart
from components.layout import format_number
from modules.analysis import kualitas as analysis
from views.analysis_sections.shared import (
    chart_block,
    insight_block,
    metric_cards,
    percentage_text,
    section_header,
    table_block,
)


def _insights(
    metrics: dict,
    completeness: pd.DataFrame,
    identities: pd.DataFrame,
    incomplete: pd.DataFrame,
) -> List[str]:
    items = [
        f"Rata-rata kelengkapan field adalah {percentage_text(metrics['rata_kelengkapan'])}.",
    ]
    if not completeness.empty:
        lowest = completeness.sort_values("persentase").iloc[0]
        items.append(
            f"Field dengan kelengkapan terendah adalah {lowest['label']} "
            f"({percentage_text(lowest['persentase'])}, {format_number(lowest['kosong'])} kosong)."
        )
        complete_fields = completeness[completeness["persentase"] == 100]
        items.append(
            f"Sebanyak {format_number(len(complete_fields))} dari {format_number(len(completeness))} field terisi lengkap."
        )
    if metrics["duplikat_baris"]:
        items.append(
            f"Terdapat {format_number(metrics['duplikat_baris'])} baris dalam "
            f"{format_number(metrics['duplikat_grup'])} grup duplikat potensial; "
            f"{format_number(metrics['duplikat_ekstra'])} baris berlebih perlu diverifikasi."
        )
    else:
        items.append("Tidak ada baris yang ditandai sebagai duplikat potensial.")
    if not identities.empty:
        invalid_total = int(identities["tidak_valid"].sum())
        if invalid_total:
            items.append(
                f"Terdapat {format_number(invalid_total)} nilai identitas mahasiswa atau dosen yang tidak sesuai pola."
            )
        else:
            items.append("Seluruh NIM dan NUPTK yang terisi sesuai pola validasi.")
    if metrics["data_tidak_lengkap"]:
        items.append(
            f"Terdapat {format_number(metrics['data_tidak_lengkap'])} prestasi dengan setidaknya satu field opsional kosong."
        )
    else:
        items.append("Seluruh field opsional pada data terfilter terisi lengkap.")
    return items


def render(frame: pd.DataFrame) -> None:
    metrics = analysis.quality_metrics(frame)
    completeness = analysis.completeness_summary(frame)
    identities = analysis.identity_validation(frame)
    certificates = analysis.certificate_completeness(frame)
    duplicates = analysis.duplicate_groups(frame)
    incomplete = analysis.incomplete_records(frame)

    metric_cards(
        [
            {
                "title": "Rata-rata Kelengkapan",
                "value": percentage_text(metrics["rata_kelengkapan"]),
                "subtitle": f"{format_number(metrics['field_lengkap'])} field terisi 100%",
                "color": "#1F9D55" if metrics["rata_kelengkapan"] >= 95 else "#D97706",
            },
            {
                "title": "Duplikat Potensial",
                "value": format_number(metrics["duplikat_baris"]),
                "subtitle": f"{format_number(metrics['duplikat_grup'])} grup, {format_number(metrics['duplikat_ekstra'])} baris berlebih",
                "color": "#D97706" if metrics["duplikat_baris"] else "#1F9D55",
            },
            {
                "title": "Data Tidak Lengkap",
                "value": format_number(metrics["data_tidak_lengkap"]),
                "subtitle": "Memiliki minimal satu field opsional kosong",
                "color": "#D97706" if metrics["data_tidak_lengkap"] else "#1F9D55",
            },
            {
                "title": "Identitas Tidak Valid",
                "value": format_number(metrics["nim_tidak_valid"] + metrics["nuptk_tidak_valid"]),
                "subtitle": f"NIM {format_number(metrics['nim_tidak_valid'])}, NUPTK {format_number(metrics['nuptk_tidak_valid'])}",
                "color": "#C0392B" if (metrics["nim_tidak_valid"] + metrics["nuptk_tidak_valid"]) else "#1F9D55",
            },
        ],
        columns=4,
    )

    section_header(
        "Kelengkapan Field",
        "Persentase field terisi. Field wajib, opsional, dan dokumen dipisahkan agar mudah ditindaklanjuti.",
    )
    if not completeness.empty:
        chart_data = completeness.copy()
        chart_data["persentase_label"] = chart_data["persentase"].map(
            lambda value: percentage_text(value)
        )
        chart_block(
            bar_chart(
                chart_data,
                x="label",
                y="persentase",
                orientation="h",
                text="persentase_label",
                color="kelompok",
                height=520,
            ),
            caption="Semakin panjang batang, semakin lengkap field tersebut.",
        )

    section_header("Tabel Kelengkapan", "Jumlah nilai terisi dan kosong untuk setiap field.")
    table_block(
        completeness,
        labels={
            "field": "Field",
            "label": "Label",
            "kelompok": "Kelompok",
            "terisi": "Terisi",
            "kosong": "Kosong",
            "persentase": "Persentase (%)",
        },
        height=430,
        empty_message="Tabel kelengkapan belum tersedia.",
    )

    section_header(
        "Validitas Identitas",
        "Validasi pola NIM (5-20 digit) dan NUPTK (16 digit).",
    )
    table_block(
        identities,
        labels={
            "field": "Field",
            "label": "Label",
            "terisi": "Terisi",
            "kosong": "Kosong",
            "tidak_valid": "Tidak Valid",
            "persentase_valid": "Persentase Valid (%)",
        },
        empty_message="Validasi identitas belum tersedia.",
    )

    with st.expander("Lihat kelengkapan dokumen pendukung", expanded=False):
        chart_data = certificates.copy()
        chart_data["persentase_label"] = chart_data["persentase"].map(
            lambda value: percentage_text(value)
        )
        chart_block(
            bar_chart(
                chart_data,
                x="label",
                y="persentase",
                orientation="h",
                text="persentase_label",
                height=320,
            ),
            caption="Ketersediaan URL dokumen pendukung pada data terfilter.",
        )
        table_block(
            certificates,
            labels={
                "field": "Field",
                "label": "Dokumen",
                "kelompok": "Kelompok",
                "terisi": "Terisi",
                "kosong": "Kosong",
                "persentase": "Persentase (%)",
            },
        )

    section_header(
        "Duplikat Potensial",
        "Baris yang memiliki kemiripan atribut dan perlu diverifikasi manual sebelum digabung atau dihapus.",
    )
    table_block(
        duplicates,
        labels={
            "prestasi_id": "ID Prestasi",
            "jumlah_baris": "Jumlah Baris",
            "nim": "NIM",
            "mahasiswa": "Mahasiswa",
            "lomba": "Lomba",
            "peringkat": "Peringkat",
            "tanggal": "Tanggal",
            "dosen": "Dosen",
            "jumlah_sertifikat": "Sertifikat",
        },
        height=300,
        empty_message="Tidak ada duplikat potensial pada data terfilter.",
    )

    section_header(
        "Field Opsional Kosong",
        "Prestasi yang masih memiliki field opsional belum terisi.",
    )
    table_block(
        incomplete,
        labels={
            "prestasi_id": "ID Prestasi",
            "mahasiswa_nama": "Mahasiswa",
            "lomba": "Lomba",
            "tahun": "Tahun",
            "field_kosong": "Field Kosong",
            "jumlah_field_kosong": "Jumlah Field Kosong",
        },
        height=300,
        empty_message="Seluruh field opsional pada data terfilter sudah terisi.",
    )

    insight_block(
        "Insight Kualitas Data",
        _insights(metrics, completeness, identities, incomplete),
    )
    st.markdown(
        """
        <div class="sapm-note">
            Kualitas data dihitung pada data setelah filter. Duplikat potensial adalah penanda sistem
            untuk verifikasi manual, bukan keputusan akhir untuk menghapus data. Validitas identitas
            memeriksa setiap NIM dan NUPTK yang dipisahkan dengan titik koma.
        </div>
        """,
        unsafe_allow_html=True,
    )
