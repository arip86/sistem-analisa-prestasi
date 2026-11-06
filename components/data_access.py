from __future__ import annotations

import logging
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from config import settings
from database.connection import database_ready
from database.repositories import (
    database_counts,
    empty_prestasi_df,
    fetch_kategori_df,
    fetch_prestasi_df,
    fetch_riwayat_import_df,
)

PUBLIC_ERROR = "Silakan coba lagi nanti atau hubungi pengelola."


@st.cache_data(ttl=90, show_spinner=False)
def load_prestasi() -> Tuple[pd.DataFrame, Optional[str]]:
    if not settings.is_configured():
        message = PUBLIC_ERROR if settings.PUBLIC_READ_ONLY else "DATABASE_URL belum dikonfigurasi."
        return empty_prestasi_df(), message
    if not database_ready():
        message = (
            PUBLIC_ERROR
            if settings.PUBLIC_READ_ONLY
            else "Tabel database belum tersedia. Jalankan inisialisasi database."
        )
        return empty_prestasi_df(), message
    try:
        return fetch_prestasi_df(), None
    except Exception as exc:
        logging.exception("Gagal memuat data prestasi.")
        message = (
            PUBLIC_ERROR
            if settings.PUBLIC_READ_ONLY
            else f"Gagal memuat data dari database: {exc}"
        )
        return empty_prestasi_df(), message


@st.cache_data(ttl=90, show_spinner=False)
def load_riwayat() -> pd.DataFrame:
    if not settings.is_configured() or not database_ready():
        return pd.DataFrame()
    try:
        return fetch_riwayat_import_df()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=90, show_spinner=False)
def load_kategori() -> pd.DataFrame:
    if not settings.is_configured() or not database_ready():
        return pd.DataFrame()
    try:
        return fetch_kategori_df()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def load_counts() -> dict:
    if not settings.is_configured() or not database_ready():
        return {"prestasi": 0, "mahasiswa": 0, "dosen": 0, "kategori": 0, "riwayat_import": 0}
    return database_counts()


def clear_caches() -> None:
    load_prestasi.clear()
    load_riwayat.clear()
    load_kategori.clear()
    load_counts.clear()
