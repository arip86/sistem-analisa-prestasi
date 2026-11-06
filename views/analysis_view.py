from __future__ import annotations

import streamlit as st

from components.data_access import load_prestasi
from components.filters import apply_filters, filter_summary_text, render_filters
from components.layout import format_number, missing_data_notice, page_header
from views.analysis_sections import capaian, dosen, kompetisi, kualitas, mahasiswa, tren


def render() -> None:
    page_header(
        "Analisis Data",
        "Eksplorasi capaian, tren, mahasiswa, dosen, kompetisi, dan kualitas data prestasi.",
    )
    frame, error = load_prestasi()
    if error:
        st.error(f"Data belum dapat dimuat: {error}")
        return
    if frame.empty:
        missing_data_notice()
        return

    filters = render_filters(frame, "analysis_data", expanded=True, columns=3)
    data = apply_filters(frame, filters)
    st.caption(
        f"{format_number(len(data))} prestasi dianalisis dari {format_number(len(frame))} total data. "
        f"Filter: {filter_summary_text(filters)}"
    )
    if data.empty:
        st.warning("Tidak ada prestasi yang sesuai dengan filter.")
        return

    tabs = st.tabs(
        [
            "Capaian",
            "Tren Waktu",
            "Mahasiswa",
            "Dosen",
            "Kompetisi",
            "Kualitas Data",
        ]
    )
    with tabs[0]:
        capaian.render(data)
    with tabs[1]:
        tren.render(data)
    with tabs[2]:
        mahasiswa.render(data)
    with tabs[3]:
        dosen.render(data)
    with tabs[4]:
        kompetisi.render(data)
    with tabs[5]:
        kualitas.render(data)
