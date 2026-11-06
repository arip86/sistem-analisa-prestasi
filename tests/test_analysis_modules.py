from __future__ import annotations

import pandas as pd
import pytest

from modules.analysis import capaian, kompetisi, kualitas, mahasiswa, tren
from modules.analysis import dosen as analysis_dosen
from modules.analysis.common import (
    lecturer_count_ranking,
    safe_pct_change,
    split_multi,
    student_consistency,
    student_count_ranking,
)

OPTIONAL_FIELDS = {
    "jumlah_unit_peserta": 10,
    "kelompok_prestasi": "INDIVIDU",
    "bentuk": "Luring",
    "url_peserta": "https://example.com/peserta",
    "url_sertifikat": "https://example.com/sertifikat",
    "url_foto_upp": "https://example.com/foto",
    "url_dokumen_undangan": "https://example.com/undangan",
    "keterangan": "Data uji",
    "dosen_url_surat_tugas": "https://example.com/surat-tugas",
}


def _row(
    prestasi_id: int,
    tanggal: str,
    level: str,
    peringkat: str,
    kategori_kode: str,
    lomba: str,
    mahasiswa_nim: str,
    mahasiswa_nama: str,
    dosen_nuptk: str,
    dosen_nama: str,
    *,
    duplicate: bool = False,
    duplicate_key: str | None = None,
    **overrides,
) -> dict:
    tanggal_ts = pd.Timestamp(tanggal)
    row = {
        "prestasi_id": prestasi_id,
        "level": level,
        "level_label": {
            "INT": "Internasional",
            "NAS": "Nasional",
            "PROV": "Provinsi",
            "KAB": "Kabupaten",
            "KOTA": "Kota",
        }[level],
        "peringkat": peringkat,
        "peringkat_label": {
            "JUARA1": "Juara 1",
            "JUARA2": "Juara 2",
            "JUARA3": "Juara 3",
            "HARAPAN1": "Harapan 1",
        }[peringkat],
        "kategori_kode": kategori_kode,
        "kategori_nama": {
            "RISNOV": "Riset dan Inovasi",
            "SENBUD": "Seni dan Budaya",
        }[kategori_kode],
        "tgl_sertifikat": tanggal_ts,
        "tahun": tanggal_ts.year,
        "bulan": tanggal_ts.month,
        "lomba": lomba,
        "cabang": f"Cabang {lomba}",
        "penyelenggara": f"Penyelenggara {lomba}",
        "mahasiswa_nim": mahasiswa_nim,
        "mahasiswa_nama": mahasiswa_nama,
        "dosen_nuptk": dosen_nuptk,
        "dosen_nama": dosen_nama,
        "is_duplicate_suspect": duplicate,
        "duplicate_group_key": duplicate_key,
        "fingerprint": f"fp-{prestasi_id}",
        "source_row_number": prestasi_id,
    }
    row.update(OPTIONAL_FIELDS)
    row.update(overrides)
    return row


@pytest.fixture
def frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _row(
                1,
                "2025-01-15",
                "NAS",
                "JUARA1",
                "RISNOV",
                "Lomba A",
                "2025001;2025002",
                "Ani; B uni",
                "1234567890123456;2234567890123456",
                "Dosen A;Dosen B",
            ),
            _row(
                2,
                "2025-03-20",
                "PROV",
                "JUARA2",
                "SENBUD",
                "Lomba B",
                "2025001",
                "Ani",
                "1234567890123456",
                "Dosen A",
                duplicate=True,
                duplicate_key="grup-1",
                url_sertifikat=None,
                keterangan="",
            ),
            _row(
                3,
                "2025-03-20",
                "PROV",
                "JUARA2",
                "SENBUD",
                "Lomba B",
                "2025001",
                "Ani",
                "1234567890123456",
                "Dosen A",
                duplicate=True,
                duplicate_key="grup-1",
                url_sertifikat=None,
                keterangan="",
            ),
            _row(
                4,
                "2026-09-10",
                "INT",
                "JUARA3",
                "RISNOV",
                "Lomba C",
                "2026003",
                "Citra",
                "3234567890123456",
                "Dosen C",
            ),
        ]
    )


def test_split_multi_and_pct_change():
    assert split_multi("2025001; 2025002") == ["2025001", "2025002"]
    assert split_multi(None) == []
    assert split_multi(float("nan")) == []
    assert safe_pct_change(1, 0) is None
    assert safe_pct_change(0, 0) == 0.0
    assert safe_pct_change(150, 100) == 50.0


def test_student_and_lecturer_rankings(frame):
    students = student_count_ranking(frame)
    assert len(students) == 3
    assert students.iloc[0]["nim"] == "2025001"
    assert students.iloc[0]["jumlah_prestasi"] == 3
    assert students.iloc[0]["poin"] == 17
    assert students.iloc[0]["juara1"] == 1

    lecturers = lecturer_count_ranking(frame)
    assert lecturers.iloc[0]["nuptk"] == "1234567890123456"
    assert lecturers.iloc[0]["jumlah_prestasi"] == 3
    assert lecturers.iloc[0]["jumlah_mahasiswa"] == 2
    assert lecturers.iloc[0]["poin"] == 17


def test_student_consistency_uses_active_months_and_span(frame):
    consistency = student_consistency(frame)
    ani = consistency[consistency["nim"] == "2025001"].iloc[0]
    assert ani["bulan_aktif"] == 2
    assert ani["rentang_bulan"] == 3
    assert ani["rasio_konsistensi"] == pytest.approx(2 / 3)


def test_capaian_summaries(frame):
    metrics = capaian.summary_metrics(frame)
    assert metrics["total_prestasi"] == 4
    assert metrics["total_mahasiswa"] == 3
    assert metrics["total_dosen"] == 3
    assert metrics["total_kompetisi"] == 3

    yearly = capaian.yearly_summary(frame)
    assert yearly["tahun"].tolist() == [2025, 2026]
    assert yearly.loc[yearly["tahun"] == 2025, "jumlah_prestasi"].iloc[0] == 3

    categories = capaian.category_summary(frame)
    risnov = categories[categories["kategori_kode"] == "RISNOV"].iloc[0]
    assert risnov["jumlah_prestasi"] == 2
    assert risnov["mahasiswa_unik"] == 3
    assert risnov["kompetisi_unik"] == 2
    assert risnov["poin"] == 14

    levels = capaian.level_summary(frame)
    assert levels.iloc[0]["level"] == "INT"
    assert levels["jumlah_prestasi"].sum() == 4

    matrix = capaian.category_level_matrix(frame)
    assert not matrix.empty
    assert set(matrix["level_label"]) == {"Nasional", "Provinsi", "Internasional"}


def test_tren_periods_and_comparison(frame):
    yearly = tren.period_summary(frame, "Tahunan")
    assert yearly["periode"].tolist() == ["2025", "2026"]
    assert yearly["jumlah_prestasi"].tolist() == [3, 1]
    assert yearly["selisih"].iloc[-1] == -2
    assert yearly["persentase"].iloc[-1] == pytest.approx(-66.6666667)

    comparison = tren.period_comparison(frame, "Tahunan", "2025", "2026")
    assert comparison["jumlah_pertama"] == 3
    assert comparison["jumlah_kedua"] == 1
    assert comparison["selisih"] == -2

    monthly = tren.monthly_by_year(frame)
    assert len(monthly[monthly["tahun"] == 2025]) == 12
    assert monthly[(monthly["tahun"] == 2025) & (monthly["bulan"] == 1)][
        "jumlah_prestasi"
    ].iloc[0] == 1
    assert monthly[(monthly["tahun"] == 2025) & (monthly["bulan"] == 2)][
        "jumlah_prestasi"
    ].iloc[0] == 0
    assert monthly[(monthly["tahun"] == 2025) & (monthly["bulan"] == 3)][
        "jumlah_prestasi"
    ].iloc[0] == 2

    metrics = tren.trend_metrics(frame, "Tahunan")
    assert metrics["periode"] == 2
    assert metrics["puncak"] == "2025"
    assert metrics["prestasi_puncak"] == 3


def test_mahasiswa_and_dosen_modules(frame):
    student_metrics = mahasiswa.metrics(frame)
    assert student_metrics["total_mahasiswa"] == 3
    assert student_metrics["mahasiswa_multiple"] == 1
    assert student_metrics["prestasi_kelompok"] == 0

    distribution = mahasiswa.distribution(frame)
    assert distribution[distribution["jumlah_prestasi"] == 1]["jumlah_mahasiswa"].iloc[0] == 2

    activity = mahasiswa.student_activity(frame)
    ani = activity[activity["nim"] == "2025001"].iloc[0]
    assert ani["jumlah_dosen"] == 2

    lecturer_metrics = analysis_dosen.metrics(frame)
    assert lecturer_metrics["total_dosen"] == 3
    assert lecturer_metrics["mahasiswa_terbanyak"] == 2
    assert not analysis_dosen.student_distribution(frame).empty
    assert not analysis_dosen.distribution(frame, "level_label").empty


def test_kompetisi_module(frame):
    table = kompetisi.competition_table(frame)
    assert len(table) == 3
    lomba_b = table[table["lomba"] == "Lomba B"].iloc[0]
    assert lomba_b["jumlah_prestasi"] == 2
    assert lomba_b["jumlah_mahasiswa"] == 1

    levels = kompetisi.level_summary(frame)
    assert levels["jumlah_kompetisi"].sum() == 3
    organizers = kompetisi.organizer_summary(frame)
    assert not organizers.empty
    branches = kompetisi.branch_summary(frame)
    assert not branches.empty
    recurring = kompetisi.recurring_competitions(frame)
    assert len(recurring) == 3

    metrics = kompetisi.metrics(frame)
    assert metrics["total_lomba"] == 3
    assert metrics["total_kompetisi"] == 3


def test_kualitas_module(frame):
    metrics = kualitas.quality_metrics(frame)
    assert metrics["total_prestasi"] == 4
    assert metrics["duplikat_baris"] == 2
    assert metrics["duplikat_grup"] == 1
    assert metrics["duplikat_ekstra"] == 1
    assert metrics["data_tidak_lengkap"] == 2

    completeness = kualitas.field_completeness(frame)
    url = completeness[completeness["field"] == "url_sertifikat"].iloc[0]
    assert url["terisi"] == 2
    assert url["kosong"] == 2
    assert url["persentase"] == 50.0

    duplicates = kualitas.duplicate_groups(frame)
    assert len(duplicates) == 1
    assert duplicates.iloc[0]["jumlah_baris"] == 2

    identities = kualitas.identity_validation(frame)
    assert identities["tidak_valid"].sum() == 0

    invalid_frame = frame.copy()
    invalid_frame.loc[invalid_frame.index[0], "mahasiswa_nim"] = "12"
    invalid = kualitas.identity_validation(invalid_frame)
    assert invalid[invalid["field"] == "mahasiswa_nim"].iloc[0]["tidak_valid"] == 1
