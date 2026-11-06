from __future__ import annotations

import re

import pandas as pd
import pytest

from modules.anonymizer import URL_PLACEHOLDER, anonymize_dataframe
from modules.data_normalizer import is_valid_url

SALT = "test-salt-yang-panjang-dan-acak"


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "mahasiswa_nim": "1111111111; 2222222222",
                "mahasiswa_nama": "Budi Santoso; Siti Aminah",
                "dosen_nuptk": "1234567890123456",
                "dosen_nama": "Dosen Pertama",
                "url_peserta": "https://example.com/peserta/1",
                "url_sertifikat": "https://example.com/sertifikat/1",
                "url_foto_upp": "",
                "url_dokumen_undangan": "https://example.com/undangan/1",
                "dosen_url_surat_tugas": "https://example.com/surat/1",
                "keterangan": "Juara 1",
            },
            {
                "mahasiswa_nim": "3333333333",
                "mahasiswa_nama": "Budi Santoso",
                "dosen_nuptk": "1234567890123456",
                "dosen_nama": "Dosen Pertama",
                "url_peserta": "https://example.com/peserta/2",
                "url_sertifikat": "https://example.com/sertifikat/2",
                "url_foto_upp": "https://example.com/foto/2",
                "url_dokumen_undangan": "https://example.com/undangan/2",
                "dosen_url_surat_tugas": "https://example.com/surat/2",
                "keterangan": "Juara 2",
            },
            {
                "mahasiswa_nim": "4444444444",
                "mahasiswa_nama": "Siti Aminah",
                "dosen_nuptk": "6543210987654321",
                "dosen_nama": "Dosen Kedua",
                "url_peserta": "https://example.com/peserta/3",
                "url_sertifikat": "https://example.com/sertifikat/3",
                "url_foto_upp": "https://example.com/foto/3",
                "url_dokumen_undangan": "https://example.com/undangan/3",
                "dosen_url_surat_tugas": "https://example.com/surat/3",
                "keterangan": "Juara 3",
            },
        ]
    )


def _tokens(value: str) -> list[str]:
    return [token.strip() for token in str(value).split(";") if token.strip()]


def test_anonymizer_removes_direct_identifiers():
    result = anonymize_dataframe(_frame(), SALT)
    text = " ".join(
        str(value)
        for column in result.columns
        for value in result[column].tolist()
        if value is not None
    )
    for original in (
        "Budi Santoso",
        "Siti Aminah",
        "Dosen Pertama",
        "Dosen Kedua",
        "1111111111",
        "2222222222",
        "3333333333",
        "4444444444",
        "1234567890123456",
        "6543210987654321",
        "example.com",
        "Juara 1",
    ):
        assert original not in text


def test_anonymizer_uses_valid_consistent_aliases():
    result = anonymize_dataframe(_frame(), SALT)

    for value in result["mahasiswa_nim"]:
        for token in _tokens(value):
            assert re.fullmatch(r"\d{10}", token)
    for value in result["dosen_nuptk"]:
        for token in _tokens(value):
            assert re.fullmatch(r"\d{16}", token)
    for value in result["mahasiswa_nama"]:
        for token in _tokens(value):
            assert re.fullmatch(r"Mahasiswa \d{3}", token)
    for value in result["dosen_nama"]:
        for token in _tokens(value):
            assert re.fullmatch(r"Dosen \d{3}", token)

    first_row_ids = _tokens(result.loc[0, "mahasiswa_nim"])
    second_row_ids = _tokens(result.loc[1, "mahasiswa_nim"])
    assert first_row_ids[0] != second_row_ids[0]

    first_row_names = _tokens(result.loc[0, "mahasiswa_nama"])
    second_row_names = _tokens(result.loc[1, "mahasiswa_nama"])
    assert first_row_names[0] != second_row_names[0]

    assert len({token for value in result["mahasiswa_nim"] for token in _tokens(value)}) == 4
    assert len({token for value in result["dosen_nuptk"] for token in _tokens(value)}) == 2


def test_anonymizer_masks_urls_and_keterangan():
    result = anonymize_dataframe(_frame(), SALT)
    for column in (
        "url_peserta",
        "url_sertifikat",
        "url_dokumen_undangan",
        "dosen_url_surat_tugas",
    ):
        for value in result[column]:
            assert str(value).startswith(URL_PLACEHOLDER)
            assert is_valid_url(str(value))
    assert result["url_foto_upp"].tolist()[0] == ""
    assert set(result["keterangan"]) == {"Disamarkan"}


def test_anonymizer_is_deterministic_and_salt_dependent():
    first = anonymize_dataframe(_frame(), SALT)
    second = anonymize_dataframe(_frame(), SALT)
    third = anonymize_dataframe(_frame(), "salt-lain")

    pd.testing.assert_frame_equal(first, second)
    assert first["mahasiswa_nim"].tolist() != third["mahasiswa_nim"].tolist()


def test_anonymizer_clears_identity_fingerprints():
    frame = _frame()
    frame["fingerprint"] = "hash-asli"
    frame["duplicate_group_key"] = "grup-asli"
    result = anonymize_dataframe(frame, SALT)
    assert result["fingerprint"].isna().all()
    assert result["duplicate_group_key"].isna().all()


def test_anonymizer_requires_salt():
    with pytest.raises(ValueError, match="ANONYMIZATION_SALT"):
        anonymize_dataframe(_frame(), "")
