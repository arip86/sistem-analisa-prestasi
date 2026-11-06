from __future__ import annotations

import pandas as pd

from modules.analytics import (
    add_points,
    category_summary,
    dosen_ranking,
    filter_data,
    level_counts,
    peringkat_counts,
    student_ranking,
    summary_metrics,
    year_counts,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "prestasi_id": 1,
                "level": "NAS",
                "level_label": "Nasional",
                "peringkat": "JUARA1",
                "peringkat_label": "Juara 1",
                "kategori_kode": "RISNOV",
                "kategori_nama": "Riset dan Inovasi",
                "tgl_sertifikat": pd.Timestamp("2025-01-10"),
                "tahun": 2025,
                "lomba": "Lomba A",
                "mahasiswa_nim": "001",
                "mahasiswa_nama": "Ani",
                "dosen_nuptk": "111",
                "dosen_nama": "Dosen A",
                "is_duplicate_suspect": False,
            },
            {
                "prestasi_id": 2,
                "level": "INT",
                "level_label": "Internasional",
                "peringkat": "JUARA2",
                "peringkat_label": "Juara 2",
                "kategori_kode": "RISNOV",
                "kategori_nama": "Riset dan Inovasi",
                "tgl_sertifikat": pd.Timestamp("2025-02-11"),
                "tahun": 2025,
                "lomba": "Lomba A",
                "mahasiswa_nim": "001",
                "mahasiswa_nama": "Ani",
                "dosen_nuptk": "111",
                "dosen_nama": "Dosen A",
                "is_duplicate_suspect": True,
            },
            {
                "prestasi_id": 3,
                "level": "PROV",
                "level_label": "Provinsi",
                "peringkat": "JUARA3",
                "peringkat_label": "Juara 3",
                "kategori_kode": "SENBUD",
                "kategori_nama": "Seni dan Budaya",
                "tgl_sertifikat": pd.Timestamp("2026-03-12"),
                "tahun": 2026,
                "lomba": "Lomba B",
                "mahasiswa_nim": "002",
                "mahasiswa_nama": "Budi",
                "dosen_nuptk": "222",
                "dosen_nama": "Dosen B",
                "is_duplicate_suspect": False,
            },
        ]
    )


def test_add_points():
    data = add_points(_frame())
    assert data["poin"].tolist() == [9, 10, 2]


def test_summary_metrics():
    metrics = summary_metrics(_frame())
    assert metrics["total_prestasi"] == 3
    assert metrics["total_mahasiswa"] == 2
    assert metrics["total_dosen"] == 2
    assert metrics["total_kompetisi"] == 2
    assert metrics["juara1"] == 1
    assert metrics["potensi_duplikat"] == 1


def test_filter_data():
    data = filter_data(_frame(), kategori=["RISNOV"], level=["INT"])
    assert len(data) == 1
    assert data.iloc[0]["prestasi_id"] == 2


def test_student_ranking():
    ranking = student_ranking(_frame())
    assert ranking.iloc[0]["nim"] == "001"
    assert ranking.iloc[0]["poin"] == 19
    assert ranking.iloc[0]["jumlah_prestasi"] == 2
    assert ranking.iloc[0]["ranking"] == 1
    assert ranking.iloc[0]["juara1"] == 1


def test_dosen_ranking():
    ranking = dosen_ranking(_frame())
    assert ranking.iloc[0]["nuptk"] == "111"
    assert ranking.iloc[0]["poin"] == 19
    assert ranking.iloc[0]["jumlah_mahasiswa"] == 1


def test_category_and_level_summaries():
    categories = category_summary(_frame())
    assert set(categories["kategori_kode"]) == {"RISNOV", "SENBUD"}
    risnov = categories[categories["kategori_kode"] == "RISNOV"].iloc[0]
    assert risnov["jumlah_prestasi"] == 2
    assert risnov["poin"] == 19
    assert "RISNOV" in risnov["kategori"]
    assert "Riset dan Inovasi" in risnov["kategori"]

    levels = level_counts(_frame())
    assert levels.iloc[0]["level"] == "INT"
    assert peringkat_counts(_frame()).iloc[0]["peringkat"] == "JUARA1"
    assert year_counts(_frame())["tahun"].tolist() == [2025, 2026]
