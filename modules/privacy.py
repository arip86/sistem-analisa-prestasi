from __future__ import annotations

from typing import Any

import pandas as pd

VISIBLE_NIM_PREFIX = 4


def _empty_value(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and not value.strip()


def _mask_single(value: str) -> str:
    text = value.strip()
    if not text:
        return "-"
    if len(text) <= VISIBLE_NIM_PREFIX:
        return "*" * len(text)
    return text[:VISIBLE_NIM_PREFIX] + "*" * (len(text) - VISIBLE_NIM_PREFIX)


def mask_nim(value: Any) -> str:
    if _empty_value(value):
        return "-"
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))
    else:
        text = str(value).strip()
    return "; ".join(_mask_single(part) for part in text.split(";"))


def mask_nim_column(frame: pd.DataFrame, column: str = "nim") -> pd.DataFrame:
    data = frame.copy()
    if column in data.columns:
        data[column] = data[column].map(mask_nim)
    return data
