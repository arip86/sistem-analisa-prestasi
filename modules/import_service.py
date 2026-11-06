from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy import select

from config.constants import CATEGORY_LABELS
from database.connection import session_scope
from database.models import (
    Dosen,
    KategoriPrestasi,
    Mahasiswa,
    Prestasi,
    RiwayatImport,
    prestasi_dosen,
    prestasi_mahasiswa,
)


def generate_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _to_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            pass
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text or None


def _optional_bool(value: Any) -> bool:
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return bool(value)


def import_valid_dataframe(
    valid: pd.DataFrame,
    nama_file: str,
    file_hash: str,
    sheet_name: Optional[str],
    total_rows: int,
    invalid_rows: int,
    existing_duplicates: int,
    duplicate_suspects: int,
) -> Dict[str, Any]:
    if valid.empty:
        raise ValueError("Tidak ada baris valid untuk diimpor.")

    berhasil = 0
    skipped = 0
    with session_scope() as session:
        batch = RiwayatImport(
            nama_file=nama_file,
            file_hash=file_hash,
            sheet_name=sheet_name,
            total_baris=total_rows,
            berhasil=0,
            duplikat=existing_duplicates,
            gagal=invalid_rows,
            potensi_duplikat=duplicate_suspects,
            status="proses",
            pesan="Proses import sedang berjalan.",
        )
        session.add(batch)
        session.flush()

        kategori_map = {row.kode: row for row in session.scalars(select(KategoriPrestasi)).all()}
        mahasiswa_map = {row.nim: row for row in session.scalars(select(Mahasiswa)).all()}
        dosen_map = {row.nuptk: row for row in session.scalars(select(Dosen)).all()}
        existing_fingerprints = set(session.scalars(select(Prestasi.fingerprint)).all())

        for row in valid.to_dict("records"):
            fingerprint = str(row.get("fingerprint") or "")
            if not fingerprint or fingerprint in existing_fingerprints:
                skipped += 1
                continue

            kode = _optional_text(row.get("kategori")) or "-"
            kategori = kategori_map.get(kode)
            if kategori is None:
                kategori = KategoriPrestasi(
                    kode=kode,
                    nama=CATEGORY_LABELS.get(kode, kode),
                )
                session.add(kategori)
                session.flush()
                kategori_map[kode] = kategori

            nim = _optional_text(row.get("mahasiswa_nim")) or ""
            nama_mahasiswa = _optional_text(row.get("mahasiswa_nama")) or nim
            mahasiswa = mahasiswa_map.get(nim)
            if mahasiswa is None:
                mahasiswa = Mahasiswa(nim=nim, nama=nama_mahasiswa)
                session.add(mahasiswa)
                session.flush()
                mahasiswa_map[nim] = mahasiswa
            elif mahasiswa.nama != nama_mahasiswa and nama_mahasiswa:
                mahasiswa.nama = nama_mahasiswa

            nuptk = _optional_text(row.get("dosen_nuptk")) or ""
            nama_dosen = _optional_text(row.get("dosen_nama")) or nuptk
            dosen = dosen_map.get(nuptk)
            if dosen is None:
                dosen = Dosen(nuptk=nuptk, nama=nama_dosen)
                session.add(dosen)
                session.flush()
                dosen_map[nuptk] = dosen
            elif dosen.nama != nama_dosen and nama_dosen:
                dosen.nama = nama_dosen

            prestasi = Prestasi(
                kategori_id=kategori.id,
                riwayat_import_id=batch.id,
                level=_optional_text(row.get("level")) or "",
                lomba=_optional_text(row.get("lomba")) or "",
                cabang=_optional_text(row.get("cabang")) or "",
                penyelenggara=_optional_text(row.get("penyelenggara")) or "",
                peringkat=_optional_text(row.get("peringkat")) or "",
                jumlah_unit_peserta=_optional_int(row.get("jumlah_unit_peserta")),
                kelompok_prestasi=_optional_text(row.get("kelompok_prestasi")),
                bentuk=_optional_text(row.get("bentuk")),
                tgl_sertifikat=_to_date(row.get("tgl_sertifikat")),
                url_peserta=_optional_text(row.get("url_peserta")),
                url_sertifikat=_optional_text(row.get("url_sertifikat")),
                url_foto_upp=_optional_text(row.get("url_foto_upp")),
                url_dokumen_undangan=_optional_text(row.get("url_dokumen_undangan")),
                keterangan=_optional_text(row.get("keterangan")),
                source_row_number=_optional_int(row.get("source_row_number")),
                fingerprint=fingerprint,
                is_duplicate_suspect=_optional_bool(row.get("is_duplicate_suspect")),
                duplicate_group_key=_optional_text(row.get("duplicate_group_key")),
            )
            session.add(prestasi)
            session.flush()

            session.execute(
                prestasi_mahasiswa.insert().values(
                    prestasi_id=prestasi.id,
                    mahasiswa_id=mahasiswa.id,
                )
            )
            session.execute(
                prestasi_dosen.insert().values(
                    prestasi_id=prestasi.id,
                    dosen_id=dosen.id,
                    url_surat_tugas=_optional_text(row.get("dosen_url_surat_tugas")),
                )
            )
            existing_fingerprints.add(fingerprint)
            berhasil += 1

        batch.berhasil = berhasil
        batch.duplikat = existing_duplicates + skipped
        batch.gagal = invalid_rows
        batch.potensi_duplikat = duplicate_suspects
        if berhasil == 0:
            batch.status = "tanpa_perubahan"
            batch.pesan = "Semua baris sudah ada di database."
        elif invalid_rows > 0:
            batch.status = "sebagian"
            batch.pesan = f"{invalid_rows} baris tidak valid dan tidak diimpor."
        else:
            batch.status = "berhasil"
            batch.pesan = f"{berhasil} baris berhasil diimpor."
        batch_id = batch.id

    return {
        "batch_id": batch_id,
        "berhasil": berhasil,
        "dilewati": skipped,
        "gagal": invalid_rows,
        "duplikat": existing_duplicates + skipped,
        "potensi_duplikat": duplicate_suspects,
    }
