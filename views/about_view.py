from __future__ import annotations

import streamlit as st

from components.data_access import load_counts
from components.layout import format_number, page_header, section_title
from config import settings
from database.connection import masked_database_info


def render() -> None:
    page_header(
        "Tentang Aplikasi",
        "Informasi sumber data, metodologi perhitungan, dan kebijakan pengolahan data.",
    )

    counts = load_counts()
    left, middle, right = st.columns(3)
    with left:
        st.metric("Total prestasi", format_number(counts.get("prestasi", 0)))
    with middle:
        st.metric("Mahasiswa", format_number(counts.get("mahasiswa", 0)))
    with right:
        st.metric("Dosen", format_number(counts.get("dosen", 0)))

    if settings.PUBLIC_READ_ONLY:
        source_description = (
            "Aplikasi publik ini menggunakan dataset prestasi yang telah dianonimkan. "
            "Nama mahasiswa, NIM yang ditampilkan dalam bentuk tersamarkan, nama dosen, "
            "tautan dokumen, dan keterangan tidak ditampilkan dalam bentuk aslinya."
        )
        database_info = "PostgreSQL terkonfigurasi"
    else:
        source_description = (
            "Aplikasi ini menggunakan data riil dari file Excel sumber dan tidak menggunakan data contoh."
        )
        database_info = masked_database_info()

    left, right = st.columns(2)
    with left:
        section_title("Tujuan Aplikasi")
        st.markdown(
            f"""
            SAPM membantu pengelolaan dan analisis data prestasi mahasiswa, mulai dari impor data,
            validasi, eksplorasi detail, analisis capaian, tren, mahasiswa, dosen, kompetisi,
            kualitas data, hingga pembuatan laporan. {source_description}
            """
        )
        section_title("Sumber Data")
        if settings.PUBLIC_READ_ONLY:
            st.markdown(
                """
                Data publik berasal dari dataset prestasi yang telah melalui proses anonimisasi.
                Struktur lomba, kategori, level, peringkat, dan tanggal tetap dipertahankan untuk
                kebutuhan analisis. Identitas langsung dan tautan dokumen disamarkan.
                """
            )
        else:
            st.markdown(
                f"""
                File sumber: `{settings.EXCEL_SOURCE_FILE.name}` dengan sheet `Template Prestasi Baru`.
                Data asli tidak diubah. Normalisasi dilakukan saat proses impor untuk membersihkan spasi
                berlebih, menyelaraskan kode level dan peringkat, serta menambahkan protokol pada tautan
                yang belum memilikinya.
                """
            )
    with right:
        section_title("Metodologi Poin")
        st.markdown(
            """
            Poin prestasi dihitung dari bobot level dikalikan bobot peringkat.

            - Level: Internasional 5, Nasional 3, Provinsi 2, Kabupaten/Kota 1.
            - Peringkat: Juara 1 = 3, Juara 2 = 2, Juara 3 = 1, Harapan = 1.

            Ranking utama Analisis Data menggunakan jumlah prestasi. Urutan mahasiswa: jumlah
            prestasi, poin, lalu nama. Urutan dosen: jumlah prestasi, poin, jumlah mahasiswa, lalu
            nama. Peringkat berbasis poin tetap tersedia melalui pilihan indikator.
            """
        )
        section_title("Kebijakan Duplikat")
        st.markdown(
            """
            Baris dengan kombinasi data yang identik dilewati saat impor. Baris dengan event dan
            mahasiswa sama tetapi dosen atau sertifikat berbeda tetap diimpor dan ditandai sebagai
            duplikat potensial untuk diverifikasi manual.
            """
        )

    section_title("Status Teknis")
    st.markdown(
        f"""
        - Versi aplikasi: `{settings.APP_VERSION}`
        - Lingkungan: `{settings.APP_ENV}`
        - Database: `{database_info}`
        - Schema: `{settings.DB_SCHEMA}`
        - Batas ukuran unggah: `{settings.MAX_UPLOAD_MB} MB`
        """
    )

    with st.expander("Alur pengolahan data"):
        st.markdown(
            """
            1. File Excel atau CSV diunggah dan header kolom dideteksi otomatis.
            2. Data dinormalisasi: spasi, kode level, kode peringkat, URL, tanggal, dan angka.
            3. Validasi memeriksa kolom wajib, identitas mahasiswa dan dosen, level, peringkat, tanggal, jumlah peserta, dan URL.
            4. Fingerprint baris digunakan untuk mencegah duplikat saat impor berulang.
            5. Data valid disimpan ke PostgreSQL, lalu seluruh halaman membaca data dari database.
            """
        )

    with st.expander("Teknologi"):
        st.markdown(
            """
            Streamlit, pandas, Plotly, SQLAlchemy, PostgreSQL, dan openpyxl.
            Struktur aplikasi memisahkan konfigurasi, akses database, modul pengolahan data,
            komponen antarmuka, dan halaman fitur.
            """
        )
