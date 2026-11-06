from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from components.cards import render_kpi_grid
from components.data_access import clear_caches, load_riwayat
from components.layout import format_number, page_header, section_title
from config.constants import CATEGORY_SHORT_LABELS, OPTIONAL_COLUMNS, REQUIRED_COLUMNS
from config import settings
from database.repositories import fetch_existing_fingerprints
from modules.data_loader import DataLoadError, load_source
from modules.data_normalizer import normalize_dataframe
from modules.data_validator import validate_dataframe
from modules.date_helper import format_date_id
from modules.import_service import generate_file_hash, import_valid_dataframe


def _join_list(values: Any) -> str:
    if isinstance(values, list):
        return " | ".join(str(value) for value in values)
    return "" if values is None else str(values)


def _preview_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    columns = [
        "source_row_number",
        "mahasiswa_nim",
        "mahasiswa_nama",
        "kategori",
        "level",
        "lomba",
        "peringkat",
        "tgl_sertifikat",
        "dosen_nama",
    ]
    existing = [column for column in columns if column in frame.columns]
    data = frame[existing].copy()
    if "tgl_sertifikat" in data.columns:
        data["tgl_sertifikat"] = data["tgl_sertifikat"].map(format_date_id)
    if "kategori" in data.columns:
        data["kategori"] = data["kategori"].map(
            lambda value: f"{CATEGORY_SHORT_LABELS.get(value, value)} ({value})" if value else "-"
        )
    return data.rename(
        columns={
            "source_row_number": "Baris",
            "mahasiswa_nim": "NIM",
            "mahasiswa_nama": "Nama Mahasiswa",
            "kategori": "Kategori",
            "level": "Level",
            "lomba": "Lomba",
            "peringkat": "Peringkat",
            "tgl_sertifikat": "Tanggal",
            "dosen_nama": "Dosen",
        }
    ).head(200)


def _error_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    data = frame.copy()
    if "validation_errors" in data.columns:
        data["validation_errors"] = data["validation_errors"].map(_join_list)
    if "validation_warnings" in data.columns:
        data["validation_warnings"] = data["validation_warnings"].map(_join_list)
    columns = [
        "source_row_number",
        "mahasiswa_nim",
        "mahasiswa_nama",
        "lomba",
        "validation_errors",
        "validation_warnings",
    ]
    existing = [column for column in columns if column in data.columns]
    return data[existing].rename(
        columns={
            "source_row_number": "Baris",
            "mahasiswa_nim": "NIM",
            "mahasiswa_nama": "Nama Mahasiswa",
            "lomba": "Lomba",
            "validation_errors": "Kesalahan",
            "validation_warnings": "Peringatan",
        }
    )


def _display_riwayat() -> None:
    riwayat = load_riwayat()
    section_title("Riwayat Import", "Log proses import terakhir")
    if riwayat.empty:
        st.caption("Belum ada riwayat import.")
        return
    data = riwayat.copy()
    data["imported_at"] = pd.to_datetime(data["imported_at"], errors="coerce").dt.strftime("%d-%m-%Y %H:%M")
    data["status"] = data["status"].fillna("-").str.replace("_", " ").str.title()
    columns = {
        "imported_at": "Waktu",
        "nama_file": "File",
        "sheet_name": "Sheet",
        "total_baris": "Total",
        "berhasil": "Berhasil",
        "duplikat": "Duplikat",
        "gagal": "Gagal",
        "potensi_duplikat": "Potensi Duplikat",
        "status": "Status",
        "pesan": "Pesan",
    }
    data = data.rename(columns=columns)
    st.dataframe(
        data[list(columns.values())],
        width="stretch",
        hide_index=True,
        height=280,
    )


def render() -> None:
    if settings.PUBLIC_READ_ONLY:
        page_header("Akses Ditolak", "Halaman impor tidak tersedia pada aplikasi publik.")
        st.error("Aplikasi ini berjalan dalam mode publik hanya-baca.")
        st.stop()

    page_header(
        "Impor Data",
        "Unggah file Excel atau CSV, periksa validasi, lalu simpan data ke database.",
    )

    if "import_result" in st.session_state:
        result = st.session_state.pop("import_result")
        if result.get("berhasil", 0) > 0:
            st.success(
                f"Import selesai: {format_number(result['berhasil'])} baris berhasil disimpan, "
                f"{format_number(result['gagal'])} gagal, "
                f"{format_number(result['potensi_duplikat'])} potensi duplikat."
            )
        else:
            st.info("Tidak ada baris baru yang disimpan.")

    st.markdown(
        f"""
        <div class="sapm-note">
            Format yang didukung: <b>.xlsx</b> dan <b>.csv</b>, maksimal {settings.MAX_UPLOAD_MB} MB.
            Baris dengan fingerprint yang sudah ada akan dilewati. Duplikat potensial tetap diimpor
            dan diberi tanda untuk verifikasi manual.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Kolom wajib dan opsional"):
        st.write("Kolom wajib: " + ", ".join(REQUIRED_COLUMNS))
        st.write("Kolom opsional: " + ", ".join(OPTIONAL_COLUMNS))

    uploaded = st.file_uploader(
        "Pilih file Excel atau CSV",
        type=["xlsx", "csv"],
        accept_multiple_files=False,
        key="import_uploader",
    )

    if uploaded is not None:
        if uploaded.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
            st.error(f"Ukuran file melebihi batas {settings.MAX_UPLOAD_MB} MB.")
            _display_riwayat()
            return
        content = uploaded.getvalue()
        try:
            loaded = load_source(content, uploaded.name)
        except DataLoadError as exc:
            st.error(str(exc))
            _display_riwayat()
            return

        normalized = normalize_dataframe(loaded.frame)
        try:
            existing = fetch_existing_fingerprints()
        except Exception as exc:
            st.error(f"Tidak dapat membaca data database: {exc}")
            _display_riwayat()
            return
        validation = validate_dataframe(normalized, existing)

        st.markdown(
            f"**{uploaded.name}** | Sheet: {loaded.sheet_name or '-'} | "
            f"Header baris: {loaded.header_row_index + 1} | "
            f"Total baris: {format_number(validation.total_rows)}"
        )
        for warning in validation.warnings:
            st.warning(warning)

        render_kpi_grid(
            [
                {
                    "title": "Baris Valid",
                    "value": format_number(validation.valid_rows),
                    "subtitle": "Siap diimpor",
                    "color": "#1F9D55",
                },
                {
                    "title": "Tidak Valid",
                    "value": format_number(validation.invalid_rows),
                    "subtitle": "Tidak akan diimpor",
                    "color": "#C0392B" if validation.invalid_rows else "#1F9D55",
                },
                {
                    "title": "Duplikat Database",
                    "value": format_number(validation.existing_duplicates),
                    "subtitle": "Akan dilewati",
                    "color": "#D97706" if validation.existing_duplicates else "#1F9D55",
                },
                {
                    "title": "Duplikat Potensial",
                    "value": format_number(validation.duplicate_suspects),
                    "subtitle": "Diimpor dengan tanda",
                    "color": "#D97706" if validation.duplicate_suspects else "#1F9D55",
                },
            ]
        )

        tabs = st.tabs(["Pratinjau Valid", "Baris Bermasalah", "Duplikat Database", "Duplikat Potensial"])
        with tabs[0]:
            if validation.valid.empty:
                st.info("Tidak ada baris valid yang siap diimpor.")
            else:
                st.dataframe(_preview_frame(validation.valid), width="stretch", hide_index=True, height=340)
        with tabs[1]:
            if validation.invalid.empty:
                st.success("Tidak ada baris bermasalah.")
            else:
                st.dataframe(_error_frame(validation.invalid), width="stretch", hide_index=True, height=340)
        with tabs[2]:
            if validation.duplicates.empty:
                st.info("Tidak ada baris yang sudah ada di database.")
            else:
                st.dataframe(_preview_frame(validation.duplicates), width="stretch", hide_index=True, height=340)
        with tabs[3]:
            suspects = validation.valid[validation.valid["is_duplicate_suspect"]] if not validation.valid.empty else validation.valid
            if suspects.empty:
                st.info("Tidak ada duplikat potensial.")
            else:
                st.dataframe(_preview_frame(suspects), width="stretch", hide_index=True, height=340)

        can_import = not validation.valid.empty
        if not can_import and validation.existing_duplicates and not validation.invalid_rows:
            st.info("Semua baris pada file ini sudah ada di database.")
        if st.button("Impor ke Database", type="primary", disabled=not can_import, width="stretch"):
            with st.spinner("Menyimpan data ke database..."):
                try:
                    result = import_valid_dataframe(
                        valid=validation.valid,
                        nama_file=uploaded.name,
                        file_hash=generate_file_hash(content),
                        sheet_name=loaded.sheet_name,
                        total_rows=validation.total_rows,
                        invalid_rows=validation.invalid_rows,
                        existing_duplicates=validation.existing_duplicates,
                        duplicate_suspects=validation.duplicate_suspects,
                    )
                except Exception as exc:
                    st.error(f"Import gagal: {exc}")
                else:
                    clear_caches()
                    st.session_state["import_result"] = result
                    st.rerun()

    _display_riwayat()
