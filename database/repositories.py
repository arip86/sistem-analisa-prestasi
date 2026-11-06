from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload, selectinload

from config.constants import CATEGORY_LABELS, LEVEL_LABELS, PERINGKAT_LABELS
from database.connection import get_session, session_scope
from database.models import (
    Dosen,
    KategoriPrestasi,
    Mahasiswa,
    Prestasi,
    RiwayatImport,
    prestasi_dosen,
)

PRESTASI_COLUMNS: List[str] = [
    "prestasi_id",
    "riwayat_import_id",
    "kategori_kode",
    "kategori_nama",
    "level",
    "level_label",
    "lomba",
    "cabang",
    "penyelenggara",
    "peringkat",
    "peringkat_label",
    "jumlah_unit_peserta",
    "kelompok_prestasi",
    "bentuk",
    "tgl_sertifikat",
    "tahun",
    "bulan",
    "url_peserta",
    "url_sertifikat",
    "url_foto_upp",
    "url_dokumen_undangan",
    "keterangan",
    "mahasiswa_nim",
    "mahasiswa_nama",
    "dosen_nuptk",
    "dosen_nama",
    "dosen_url_surat_tugas",
    "source_row_number",
    "fingerprint",
    "is_duplicate_suspect",
    "duplicate_group_key",
]


def empty_prestasi_df() -> pd.DataFrame:
    return pd.DataFrame(columns=PRESTASI_COLUMNS)


def _split_join(values: List[str]) -> str:
    return "; ".join(str(value) for value in values if value)


def _prestasi_to_row(prestasi: Prestasi, surat_tugas_map: Dict[tuple, str]) -> Dict[str, Any]:
    mahasiswa_rows = sorted(prestasi.mahasiswa, key=lambda item: item.nim)
    dosen_rows = sorted(prestasi.dosen, key=lambda item: item.nama)
    tanggal = prestasi.tgl_sertifikat
    tahun = tanggal.year if tanggal else None
    bulan = tanggal.month if tanggal else None
    dosen_urls = [
        surat_tugas_map.get((prestasi.id, dosen.id), "") for dosen in dosen_rows
    ]
    return {
        "prestasi_id": prestasi.id,
        "riwayat_import_id": prestasi.riwayat_import_id,
        "kategori_kode": prestasi.kategori.kode if prestasi.kategori else None,
        "kategori_nama": prestasi.kategori.nama if prestasi.kategori else None,
        "level": prestasi.level,
        "level_label": LEVEL_LABELS.get(prestasi.level, prestasi.level),
        "lomba": prestasi.lomba,
        "cabang": prestasi.cabang,
        "penyelenggara": prestasi.penyelenggara,
        "peringkat": prestasi.peringkat,
        "peringkat_label": PERINGKAT_LABELS.get(prestasi.peringkat, prestasi.peringkat),
        "jumlah_unit_peserta": prestasi.jumlah_unit_peserta,
        "kelompok_prestasi": prestasi.kelompok_prestasi,
        "bentuk": prestasi.bentuk,
        "tgl_sertifikat": tanggal,
        "tahun": tahun,
        "bulan": bulan,
        "url_peserta": prestasi.url_peserta,
        "url_sertifikat": prestasi.url_sertifikat,
        "url_foto_upp": prestasi.url_foto_upp,
        "url_dokumen_undangan": prestasi.url_dokumen_undangan,
        "keterangan": prestasi.keterangan,
        "mahasiswa_nim": _split_join([item.nim for item in mahasiswa_rows]),
        "mahasiswa_nama": _split_join([item.nama for item in mahasiswa_rows]),
        "dosen_nuptk": _split_join([item.nuptk for item in dosen_rows]),
        "dosen_nama": _split_join([item.nama for item in dosen_rows]),
        "dosen_url_surat_tugas": _split_join(dosen_urls),
        "source_row_number": prestasi.source_row_number,
        "fingerprint": prestasi.fingerprint,
        "is_duplicate_suspect": bool(prestasi.is_duplicate_suspect),
        "duplicate_group_key": prestasi.duplicate_group_key,
    }


def fetch_prestasi_df(session: Optional[Session] = None) -> pd.DataFrame:
    owns_session = session is None
    session = session or get_session()
    try:
        statement = (
            select(Prestasi)
            .options(
                joinedload(Prestasi.kategori),
                selectinload(Prestasi.mahasiswa),
                selectinload(Prestasi.dosen),
            )
            .order_by(Prestasi.tgl_sertifikat.desc(), Prestasi.id.desc())
        )
        prestasi_rows = session.scalars(statement).unique().all()
        if not prestasi_rows:
            return empty_prestasi_df()

        surat_tugas_map: Dict[tuple, str] = {}
        for row in session.execute(select(prestasi_dosen)).mappings():
            if row["url_surat_tugas"]:
                surat_tugas_map[(row["prestasi_id"], row["dosen_id"])] = row["url_surat_tugas"]

        data = [_prestasi_to_row(item, surat_tugas_map) for item in prestasi_rows]
        frame = pd.DataFrame(data, columns=PRESTASI_COLUMNS)
        frame["tgl_sertifikat"] = pd.to_datetime(frame["tgl_sertifikat"], errors="coerce")
        frame["tahun"] = frame["tahun"].astype("Int64")
        frame["bulan"] = frame["bulan"].astype("Int64")
        frame["jumlah_unit_peserta"] = pd.to_numeric(
            frame["jumlah_unit_peserta"], errors="coerce"
        ).astype("Int64")
        return frame
    finally:
        if owns_session:
            session.close()


def fetch_riwayat_import_df(session: Optional[Session] = None) -> pd.DataFrame:
    owns_session = session is None
    session = session or get_session()
    try:
        rows = session.scalars(select(RiwayatImport).order_by(RiwayatImport.imported_at.desc())).all()
        data = [
            {
                "id": row.id,
                "nama_file": row.nama_file,
                "file_hash": row.file_hash,
                "sheet_name": row.sheet_name,
                "total_baris": row.total_baris,
                "berhasil": row.berhasil,
                "duplikat": row.duplikat,
                "gagal": row.gagal,
                "potensi_duplikat": row.potensi_duplikat,
                "status": row.status,
                "pesan": row.pesan,
                "imported_at": row.imported_at,
            }
            for row in rows
        ]
        return pd.DataFrame(data)
    finally:
        if owns_session:
            session.close()


def fetch_kategori_df(session: Optional[Session] = None) -> pd.DataFrame:
    owns_session = session is None
    session = session or get_session()
    try:
        rows = session.scalars(select(KategoriPrestasi).order_by(KategoriPrestasi.kode)).all()
        return pd.DataFrame(
            [
                {"id": row.id, "kode": row.kode, "nama": row.nama}
                for row in rows
            ]
        )
    finally:
        if owns_session:
            session.close()


def fetch_mahasiswa_df(session: Optional[Session] = None) -> pd.DataFrame:
    owns_session = session is None
    session = session or get_session()
    try:
        rows = session.scalars(select(Mahasiswa).order_by(Mahasiswa.nama)).all()
        return pd.DataFrame(
            [{"id": row.id, "nim": row.nim, "nama": row.nama} for row in rows]
        )
    finally:
        if owns_session:
            session.close()


def fetch_dosen_df(session: Optional[Session] = None) -> pd.DataFrame:
    owns_session = session is None
    session = session or get_session()
    try:
        rows = session.scalars(select(Dosen).order_by(Dosen.nama)).all()
        return pd.DataFrame(
            [{"id": row.id, "nuptk": row.nuptk, "nama": row.nama} for row in rows]
        )
    finally:
        if owns_session:
            session.close()


def fetch_existing_fingerprints(session: Optional[Session] = None) -> set[str]:
    owns_session = session is None
    session = session or get_session()
    try:
        return set(session.scalars(select(Prestasi.fingerprint)).all())
    finally:
        if owns_session:
            session.close()


def database_counts() -> Dict[str, int]:
    try:
        with session_scope() as session:
            return {
                "prestasi": int(session.scalar(text("SELECT count(*) FROM prestasi")) or 0),
                "mahasiswa": int(session.scalar(text("SELECT count(*) FROM mahasiswa")) or 0),
                "dosen": int(session.scalar(text("SELECT count(*) FROM dosen")) or 0),
                "kategori": int(session.scalar(text("SELECT count(*) FROM kategori_prestasi")) or 0),
                "riwayat_import": int(session.scalar(text("SELECT count(*) FROM riwayat_import")) or 0),
            }
    except Exception:
        return {"prestasi": 0, "mahasiswa": 0, "dosen": 0, "kategori": 0, "riwayat_import": 0}


def category_display(kode: Optional[str], nama: Optional[str] = None) -> str:
    if not kode:
        return nama or "-"
    label = CATEGORY_LABELS.get(kode, nama or kode)
    return f"{label} ({kode})"
