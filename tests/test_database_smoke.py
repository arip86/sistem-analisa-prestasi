from __future__ import annotations

import pytest

from config import settings
from database.connection import database_ready
from database.repositories import fetch_prestasi_df

pytestmark = pytest.mark.skipif(
    not settings.is_configured() or not database_ready(),
    reason="Database belum dikonfigurasi atau tabel belum dibuat.",
)


def test_database_has_prestasi_data():
    frame = fetch_prestasi_df()
    assert not frame.empty
    assert "prestasi_id" in frame.columns
    assert "mahasiswa_nim" in frame.columns
    assert "dosen_nama" in frame.columns
    assert frame["mahasiswa_nim"].notna().all()
    assert frame["dosen_nama"].notna().all()
