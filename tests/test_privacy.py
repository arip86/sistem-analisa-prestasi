from __future__ import annotations

import pandas as pd

from modules.privacy import mask_nim, mask_nim_column


def test_mask_nim_keeps_prefix():
    assert mask_nim("9000027062") == "9000******"


def test_mask_nim_handles_multiple_values():
    value = "900000001; 900000002"
    assert mask_nim(value) == "9000*****; 9000*****"


def test_mask_nim_handles_empty_values():
    assert mask_nim(None) == "-"
    assert mask_nim("") == "-"
    assert mask_nim(float("nan")) == "-"


def test_mask_nim_handles_numeric_values():
    assert mask_nim(9000027062) == "9000******"
    assert mask_nim(9000027062.0) == "9000******"


def test_mask_nim_column_does_not_modify_source():
    frame = pd.DataFrame({"nim": ["9000027062", None], "nama": ["Mahasiswa 001", "Mahasiswa 002"]})
    masked = mask_nim_column(frame)
    assert masked["nim"].tolist() == ["9000******", "-"]
    assert frame["nim"].iloc[0] == "9000027062"
