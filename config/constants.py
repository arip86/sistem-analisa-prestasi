from __future__ import annotations

from typing import Dict, List

SHEET_NAME = "Template Prestasi Baru"

REQUIRED_COLUMNS: List[str] = [
    "level",
    "kategori",
    "lomba",
    "cabang",
    "penyelenggara",
    "peringkat",
    "tgl_sertifikat",
    "mahasiswa_nim",
    "mahasiswa_nama",
    "dosen_nuptk",
    "dosen_nama",
]

OPTIONAL_COLUMNS: List[str] = [
    "jumlah_unit_peserta",
    "kelompok_prestasi",
    "bentuk",
    "url_peserta",
    "url_sertifikat",
    "url_foto_upp",
    "url_dokumen_undangan",
    "keterangan",
    "dosen_url_surat_tugas",
]

ALL_COLUMNS: List[str] = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

COLUMN_ALIASES: Dict[str, List[str]] = {
    "level": ["level", "tingkat", "tingkat_kompetisi", "tingkat_lomba"],
    "kategori": ["kategori", "category", "jenis_prestasi"],
    "lomba": ["lomba", "nama_lomba", "kompetisi", "nama_kompetisi"],
    "cabang": ["cabang", "cabang_lomba", "bidang"],
    "penyelenggara": ["penyelenggara", "organizer", "penyedia"],
    "peringkat": ["peringkat", "juara", "rank", "ranking"],
    "jumlah_unit_peserta": ["jumlah_unit_peserta", "jumlah_peserta", "unit_peserta"],
    "kelompok_prestasi": ["kelompok_prestasi", "kelompok", "jenis_kelompok"],
    "bentuk": ["bentuk", "mode", "metode"],
    "url_peserta": ["url_peserta", "tautan_peserta", "link_peserta"],
    "url_sertifikat": ["url_sertifikat", "tautan_sertifikat", "link_sertifikat", "sertifikat"],
    "tgl_sertifikat": ["tgl_sertifikat", "tanggal_sertifikat", "tanggal", "tgl"],
    "url_foto_upp": ["url_foto_upp", "foto_upp", "url_foto"],
    "url_dokumen_undangan": ["url_dokumen_undangan", "dokumen_undangan", "url_undangan"],
    "keterangan": ["keterangan", "catatan", "note"],
    "mahasiswa_nim": ["mahasiswa_nim", "nim", "nim_mahasiswa"],
    "mahasiswa_nama": ["mahasiswa_nama", "nama_mahasiswa", "nama"],
    "dosen_nuptk": ["dosen_nuptk", "nuptk", "nuptk_dosen"],
    "dosen_nama": ["dosen_nama", "nama_dosen"],
    "dosen_url_surat_tugas": ["dosen_url_surat_tugas", "url_surat_tugas", "surat_tugas"],
}

LEVEL_ALIASES = {
    "NAS": "NAS",
    "NASIONAL": "NAS",
    "NATIONAL": "NAS",
    "PROV": "PROV",
    "PROVINSI": "PROV",
    "PROVINCIAL": "PROV",
    "INT": "INT",
    "INTERNASIONAL": "INT",
    "INTERNATIONAL": "INT",
    "KAB": "KAB",
    "KABUPATEN": "KAB",
    "KOTA": "KOTA",
}

ALLOWED_LEVELS = {"NAS", "PROV", "INT", "KAB", "KOTA"}

PERINGKAT_ALIASES = {
    "JUARA1": "JUARA1",
    "JUARA 1": "JUARA1",
    "JUARA_1": "JUARA1",
    "JUARA I": "JUARA1",
    "JUARA2": "JUARA2",
    "JUARA 2": "JUARA2",
    "JUARA_2": "JUARA2",
    "JUARA II": "JUARA2",
    "JUARA3": "JUARA3",
    "JUARA 3": "JUARA3",
    "JUARA_3": "JUARA3",
    "JUARA III": "JUARA3",
    "HARAPAN1": "HARAPAN1",
    "HARAPAN 1": "HARAPAN1",
    "HARAPAN2": "HARAPAN2",
    "HARAPAN 2": "HARAPAN2",
    "HARAPAN3": "HARAPAN3",
    "HARAPAN 3": "HARAPAN3",
}

ALLOWED_PERINGKAT = {
    "JUARA1",
    "JUARA2",
    "JUARA3",
    "HARAPAN1",
    "HARAPAN2",
    "HARAPAN3",
}

PERINGKAT_LABELS = {
    "JUARA1": "Juara 1",
    "JUARA2": "Juara 2",
    "JUARA3": "Juara 3",
    "HARAPAN1": "Harapan 1",
    "HARAPAN2": "Harapan 2",
    "HARAPAN3": "Harapan 3",
}

LEVEL_LABELS = {
    "NAS": "Nasional",
    "PROV": "Provinsi",
    "INT": "Internasional",
    "KAB": "Kabupaten",
    "KOTA": "Kota",
}

CATEGORY_LABELS = {
    "RISNOVSSH": "Riset, Inovasi, Seni, Budaya, dan Sosial Humaniora",
    "RISNOV": "Riset dan Inovasi",
    "SENBUD": "Seni dan Budaya",
    "MINAT": "Minat dan Bakat",
    "OLAHRAGA": "Olahraga",
}

CATEGORY_SHORT_LABELS = {
    "RISNOVSSH": "Riset, Inovasi, Seni & Budaya",
    "RISNOV": "Riset dan Inovasi",
    "SENBUD": "Seni dan Budaya",
    "MINAT": "Minat dan Bakat",
    "OLAHRAGA": "Olahraga",
}

RANK_POINTS = {
    "JUARA1": 3,
    "JUARA2": 2,
    "JUARA3": 1,
    "HARAPAN1": 1,
    "HARAPAN2": 1,
    "HARAPAN3": 1,
}

LEVEL_POINTS = {"INT": 5, "NAS": 3, "PROV": 2, "KAB": 1, "KOTA": 1}

NIM_PATTERN = r"^\d{5,20}$"
NUPTK_PATTERN = r"^\d{16}$"

ALLOWED_UPLOAD_EXTENSIONS = {".xlsx", ".csv"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

URL_COLUMNS = [
    "url_peserta",
    "url_sertifikat",
    "url_foto_upp",
    "url_dokumen_undangan",
    "dosen_url_surat_tugas",
]

PRIMARY_COLOR = "#0B1F3A"
SECONDARY_COLOR = "#1E4E8C"
ACCENT_COLOR = "#2F80ED"
SUCCESS_COLOR = "#1F9D55"
WARNING_COLOR = "#D97706"
DANGER_COLOR = "#C0392B"
CHART_COLORS = [
    "#0B1F3A",
    "#1E4E8C",
    "#2F80ED",
    "#56A3F5",
    "#8FC3FA",
    "#1F9D55",
    "#D97706",
    "#C0392B",
    "#6B7280",
    "#9CA3AF",
]
