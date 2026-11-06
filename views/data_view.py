from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from components.data_access import load_prestasi
from components.filters import apply_filters, filter_summary_text, render_filters
from components.layout import (
    detail_card,
    format_number,
    missing_data_notice,
    page_header,
    render_links,
    section_title,
)
from config import settings
from config.constants import CATEGORY_SHORT_LABELS
from modules.data_normalizer import is_valid_url
from modules.date_helper import format_date_id
from modules.privacy import mask_nim


def _display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "Tanggal": format_date_id(row.get("tgl_sertifikat")),
                "NIM": mask_nim(row.get("mahasiswa_nim")),
                "Nama Mahasiswa": row.get("mahasiswa_nama"),
                "Kategori": CATEGORY_SHORT_LABELS.get(
                    row.get("kategori_kode"), row.get("kategori_nama") or row.get("kategori_kode")
                ),
                "Level": row.get("level_label"),
                "Lomba": row.get("lomba"),
                "Cabang": row.get("cabang"),
                "Peringkat": row.get("peringkat_label"),
                "Dosen": row.get("dosen_nama"),
                "Penyelenggara": row.get("penyelenggara"),
                "Potensi Duplikat": "Ya" if row.get("is_duplicate_suspect") else "Tidak",
            }
        )
    return pd.DataFrame(rows)


def _search(frame: pd.DataFrame, query: str) -> pd.DataFrame:
    if not query.strip():
        return frame
    searchable = frame.copy()
    if "mahasiswa_nim" in searchable.columns:
        searchable["mahasiswa_nim"] = searchable["mahasiswa_nim"].map(mask_nim)
    columns = ["mahasiswa_nim", "mahasiswa_nama", "dosen_nama", "lomba", "cabang", "penyelenggara", "keterangan"]
    mask = pd.Series(False, index=searchable.index)
    keyword = query.strip().lower()
    for column in columns:
        if column in searchable.columns:
            mask = mask | searchable[column].fillna("").astype(str).str.lower().str.contains(keyword, regex=False)
    return frame[mask].reset_index(drop=True)


def _selected_row(frame: pd.DataFrame, key: str) -> Optional[pd.Series]:
    if frame.empty:
        return None
    labels = {
        int(row["prestasi_id"]): (
            f"Baris {row.get('source_row_number')} | {mask_nim(row.get('mahasiswa_nim'))} - "
            f"{row.get('mahasiswa_nama')} | {row.get('lomba')}"
        )
        for _, row in frame.iterrows()
    }
    selected_id = st.selectbox(
        "Pilih prestasi",
        options=list(labels.keys()),
        format_func=lambda value: labels.get(value, str(value)),
        key=key,
    )
    matches = frame[frame["prestasi_id"] == selected_id]
    if matches.empty:
        return None
    return matches.iloc[0]


def _render_detail(row: pd.Series) -> None:
    left, right = st.columns(2)
    with left:
        detail_card(
            "Informasi Prestasi",
            [
                ("Kategori", f"{CATEGORY_SHORT_LABELS.get(row.get('kategori_kode'), row.get('kategori_nama'))} ({row.get('kategori_kode')})"),
                ("Level", row.get("level_label")),
                ("Lomba", row.get("lomba")),
                ("Cabang", row.get("cabang")),
                ("Penyelenggara", row.get("penyelenggara")),
                ("Peringkat", row.get("peringkat_label")),
                ("Tanggal Sertifikat", format_date_id(row.get("tgl_sertifikat"))),
                ("Jumlah Unit Peserta", row.get("jumlah_unit_peserta")),
                ("Kelompok", row.get("kelompok_prestasi")),
                ("Bentuk", row.get("bentuk")),
                ("Keterangan", row.get("keterangan")),
                ("Potensi Duplikat", "Ya" if row.get("is_duplicate_suspect") else "Tidak"),
            ],
        )
    with right:
        detail_card(
            "Mahasiswa dan Dosen",
            [
                ("NIM", mask_nim(row.get("mahasiswa_nim"))),
                ("Nama Mahasiswa", row.get("mahasiswa_nama")),
                ("Nama Dosen", row.get("dosen_nama")),
                ("Sumber Baris", row.get("source_row_number")),
                ("ID Prestasi", row.get("prestasi_id")),
            ],
        )

    if settings.PUBLIC_READ_ONLY:
        st.caption("Tautan dokumen tidak ditampilkan pada aplikasi publik.")
        return

    link_items = [
        ("Buka Link Peserta", row.get("url_peserta")),
        ("Buka Sertifikat", row.get("url_sertifikat")),
        ("Buka Foto", row.get("url_foto_upp")),
        ("Buka Dokumen Undangan", row.get("url_dokumen_undangan")),
        ("Buka Surat Tugas", row.get("dosen_url_surat_tugas")),
    ]
    valid_links = [(label, url) for label, url in link_items if url and is_valid_url(str(url))]
    if valid_links:
        section_title("Tautan Terkait")
        columns = st.columns(min(3, len(valid_links)))
        for index, (label, url) in enumerate(valid_links):
            with columns[index % len(columns)]:
                render_links(label, str(url), key=f"detail_link_{index}")
    else:
        st.caption("Tidak ada tautan yang valid pada data prestasi ini.")


def render() -> None:
    page_header(
        "Data Prestasi",
        "Telusuri, filter, dan periksa detail setiap baris prestasi mahasiswa.",
    )
    frame, error = load_prestasi()
    if error:
        st.error(f"Data belum dapat dimuat: {error}")
        return
    if frame.empty:
        missing_data_notice()
        return

    filters = render_filters(frame, "data", show_duplicate=True)
    data = apply_filters(frame, filters)

    search_columns = st.columns([2.2, 1])
    with search_columns[0]:
        query = st.text_input(
            "Cari data",
            placeholder="Cari NIM tersamarkan, nama mahasiswa, dosen, lomba, cabang, atau penyelenggara",
            key="data_search",
        )
    with search_columns[1]:
        st.caption("Filter aktif")
        st.write(filter_summary_text(filters))

    data = _search(data, query)
    if data.empty:
        st.warning("Tidak ada data yang sesuai dengan pencarian dan filter.")
        return

    display = _display_frame(data)
    duplicate_count = int(data["is_duplicate_suspect"].sum())
    caption = f"{format_number(len(data))} prestasi ditampilkan"
    if duplicate_count:
        caption += f" | {format_number(duplicate_count)} ditandai sebagai duplikat potensial"
    st.caption(caption)

    table_tab, detail_tab = st.tabs(["Tabel Prestasi", "Detail Prestasi"])
    with table_tab:
        st.dataframe(
            display,
            width="stretch",
            hide_index=True,
            height=560,
            column_config={
                "Potensi Duplikat": st.column_config.TextColumn(
                    "Potensi Duplikat",
                    help="Baris dengan event dan mahasiswa sama tetapi dosen atau sertifikat berbeda.",
                ),
            },
        )
    with detail_tab:
        row = _selected_row(data, "data_detail_id")
        if row is None:
            st.info("Pilih satu prestasi untuk melihat detail.")
        else:
            _render_detail(row)
