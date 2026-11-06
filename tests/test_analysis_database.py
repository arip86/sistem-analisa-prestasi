from __future__ import annotations

import pytest

from config import settings
from database.connection import database_ready
from database.repositories import fetch_prestasi_df
from modules.analysis import capaian, kompetisi, kualitas, mahasiswa

pytestmark = pytest.mark.skipif(
    not settings.is_configured() or not database_ready(),
    reason="Database belum dikonfigurasi atau tabel belum dibuat.",
)


def test_analysis_matches_current_database():
    frame = fetch_prestasi_df()
    metrics = capaian.summary_metrics(frame)
    assert metrics["total_prestasi"] == 292
    assert metrics["total_mahasiswa"] == 273
    assert metrics["total_dosen"] == 59
    assert metrics["total_kompetisi"] == 43

    competition_metrics = kompetisi.metrics(frame)
    assert competition_metrics["total_lomba"] == 42
    assert competition_metrics["total_penyelenggara"] == 25
    assert competition_metrics["total_cabang"] == 21

    student_metrics = mahasiswa.metrics(frame)
    assert student_metrics["total_mahasiswa"] == 273
    assert student_metrics["mahasiswa_multiple"] == 18
    assert student_metrics["mahasiswa_internasional"] == 0
    assert student_metrics["prestasi_individu"] == 292
    assert student_metrics["prestasi_kelompok"] == 0

    quality = kualitas.quality_metrics(frame)
    assert quality["duplikat_baris"] == 8
    assert quality["duplikat_grup"] == 4
    assert quality["duplikat_ekstra"] == 4
    assert quality["rata_kelengkapan"] == 100.0
    assert quality["data_tidak_lengkap"] == 0
    assert quality["nim_tidak_valid"] == 0
    assert quality["nuptk_tidak_valid"] == 0
