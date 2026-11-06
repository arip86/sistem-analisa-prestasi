from __future__ import annotations

import re
from typing import Any, Optional

import pandas as pd

TEXT_COLUMNS = [
    "level",
    "kategori",
    "lomba",
    "cabang",
    "penyelenggara",
    "peringkat",
    "kelompok_prestasi",
    "bentuk",
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
]


def clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).replace("\u00a0", " ").strip()
    if not text or text.lower() in {"nan", "nat", "none", "null"}:
        return None
    return re.sub(r"\s+", " ", text)


def clean_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    for column in TEXT_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].map(clean_text)
    return cleaned
