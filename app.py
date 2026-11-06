from __future__ import annotations

import streamlit as st

from components.data_access import clear_caches, load_counts
from components.layout import format_number, load_css
from config import settings
from database.connection import check_connection, database_ready
from views import analysis_view, about_view, dashboard, data_view, import_view, report_view

st.set_page_config(
    page_title=f"{settings.APP_NAME} - {settings.APP_LONG_NAME}",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _database_badge() -> str:
    if not settings.is_configured():
        return '<span class="sapm-badge sapm-badge-danger">Belum dikonfigurasi</span>'
    if not check_connection():
        return '<span class="sapm-badge sapm-badge-danger">Koneksi gagal</span>'
    if not database_ready():
        return '<span class="sapm-badge sapm-badge-warning">Tabel belum siap</span>'
    return '<span class="sapm-badge sapm-badge-success">Terhubung</span>'


def _render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="sapm-brand">
                <div class="sapm-brand-title">SAPM</div>
                <div class="sapm-brand-sub">Sistem Analisis Prestasi Mahasiswa</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        pages = [
            "Dasbor",
            "Data Prestasi",
            "Analisis Data",
            "Laporan",
        ]
        if not settings.PUBLIC_READ_ONLY:
            pages.append("Impor Data")
        pages.append("Tentang")
        page = st.radio("Navigasi", pages, label_visibility="collapsed")
        st.divider()

        counts = load_counts()
        st.markdown(
            f"""
            <div class="sapm-sidebar-stats">
                <div class="row"><span>Prestasi</span><span class="value">{format_number(counts.get('prestasi', 0))}</span></div>
                <div class="row"><span>Mahasiswa</span><span class="value">{format_number(counts.get('mahasiswa', 0))}</span></div>
                <div class="row"><span>Dosen</span><span class="value">{format_number(counts.get('dosen', 0))}</span></div>
                <div class="row"><span>Kategori</span><span class="value">{format_number(counts.get('kategori', 0))}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='margin-top:0.7rem'>Status database</div>", unsafe_allow_html=True)
        st.markdown(_database_badge(), unsafe_allow_html=True)
        if settings.is_configured() and check_connection() and not database_ready():
            st.caption("Jalankan `python scripts/init_db.py` untuk membuat tabel.")
        st.divider()
        if st.button("Muat Ulang Data", width="stretch"):
            clear_caches()
            st.rerun()
        st.caption(f"SAPM v{settings.APP_VERSION}")
    return page


def main() -> None:
    load_css()
    page = _render_sidebar()
    if page == "Dasbor":
        dashboard.render()
    elif page == "Data Prestasi":
        data_view.render()
    elif page == "Analisis Data":
        analysis_view.render()
    elif page == "Laporan":
        report_view.render()
    elif page == "Impor Data":
        import_view.render()
    else:
        about_view.render()


if __name__ == "__main__":
    main()
