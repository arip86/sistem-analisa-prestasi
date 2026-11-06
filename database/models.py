from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


prestasi_mahasiswa = Table(
    "prestasi_mahasiswa",
    Base.metadata,
    Column("prestasi_id", ForeignKey("prestasi.id", ondelete="CASCADE"), primary_key=True),
    Column("mahasiswa_id", ForeignKey("mahasiswa.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_prestasi_mahasiswa_mahasiswa_id", "mahasiswa_id"),
)

prestasi_dosen = Table(
    "prestasi_dosen",
    Base.metadata,
    Column("prestasi_id", ForeignKey("prestasi.id", ondelete="CASCADE"), primary_key=True),
    Column("dosen_id", ForeignKey("dosen.id", ondelete="CASCADE"), primary_key=True),
    Column("url_surat_tugas", Text, nullable=True),
    Index("ix_prestasi_dosen_dosen_id", "dosen_id"),
)


class Mahasiswa(Base):
    __tablename__ = "mahasiswa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nim: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    prestasi: Mapped[List["Prestasi"]] = relationship(
        "Prestasi",
        secondary=prestasi_mahasiswa,
        back_populates="mahasiswa",
        lazy="selectin",
    )


class Dosen(Base):
    __tablename__ = "dosen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nuptk: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    prestasi: Mapped[List["Prestasi"]] = relationship(
        "Prestasi",
        secondary=prestasi_dosen,
        back_populates="dosen",
        lazy="selectin",
    )


class KategoriPrestasi(Base):
    __tablename__ = "kategori_prestasi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kode: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    nama: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    prestasi: Mapped[List["Prestasi"]] = relationship("Prestasi", back_populates="kategori")


class RiwayatImport(Base):
    __tablename__ = "riwayat_import"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nama_file: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sheet_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    total_baris: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    berhasil: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplikat: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gagal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    potensi_duplikat: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="berhasil", index=True)
    pesan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    prestasi: Mapped[List["Prestasi"]] = relationship("Prestasi", back_populates="riwayat_import")


class Prestasi(Base):
    __tablename__ = "prestasi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kategori_id: Mapped[int] = mapped_column(ForeignKey("kategori_prestasi.id"), nullable=False, index=True)
    riwayat_import_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("riwayat_import.id", ondelete="SET NULL"), nullable=True, index=True
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    lomba: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    cabang: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    penyelenggara: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    peringkat: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    jumlah_unit_peserta: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    kelompok_prestasi: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    bentuk: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    tgl_sertifikat: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    url_peserta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_sertifikat: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_foto_upp: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_dokumen_undangan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keterangan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    is_duplicate_suspect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    duplicate_group_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    kategori: Mapped["KategoriPrestasi"] = relationship("KategoriPrestasi", back_populates="prestasi", lazy="joined")
    riwayat_import: Mapped[Optional["RiwayatImport"]] = relationship("RiwayatImport", back_populates="prestasi")
    mahasiswa: Mapped[List["Mahasiswa"]] = relationship(
        "Mahasiswa",
        secondary=prestasi_mahasiswa,
        back_populates="prestasi",
        lazy="selectin",
    )
    dosen: Mapped[List["Dosen"]] = relationship(
        "Dosen",
        secondary=prestasi_dosen,
        back_populates="prestasi",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_prestasi_tanggal_level", "tgl_sertifikat", "level"),
        Index("ix_prestasi_kategori_peringkat", "kategori_id", "peringkat"),
    )
