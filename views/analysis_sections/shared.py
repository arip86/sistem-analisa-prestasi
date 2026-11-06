from __future__ import annotations

import html
from typing import Any, Dict, Iterable, Optional, Sequence

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.cards import render_kpi_grid
from components.layout import format_number, section_title


def metric_cards(items: Sequence[Dict[str, Any]], columns: int = 4) -> None:
    render_kpi_grid(list(items), columns=columns)


def chart_block(
    figure: go.Figure,
    caption: Optional[str] = None,
    note: Optional[str] = None,
) -> None:
    st.plotly_chart(figure, width="stretch")
    if caption:
        st.caption(caption)
    if note:
        st.markdown(f'<div class="sapm-note">{html.escape(note)}</div>', unsafe_allow_html=True)


def table_block(
    frame: pd.DataFrame,
    labels: Optional[Dict[str, str]] = None,
    height: Optional[int] = None,
    empty_message: str = "Tidak ada data untuk ditampilkan.",
) -> None:
    if frame.empty:
        st.info(empty_message)
        return
    display = frame.rename(columns=labels) if labels else frame
    kwargs = {"height": height} if height is not None else {}
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        **kwargs,
    )


def insight_block(title: str, items: Iterable[str]) -> None:
    values = [item for item in items if item]
    if not values:
        return
    cards = "".join(
        f'<div class="sapm-insight-item"><span>{index}</span><p>{html.escape(item)}</p></div>'
        for index, item in enumerate(values, start=1)
    )
    st.markdown(
        f"""
        <div class="sapm-insight-panel">
            <div class="sapm-insight-title">{html.escape(title)}</div>
            {cards}
        </div>
        """,
        unsafe_allow_html=True,
    )


def percentage_text(value: Any, decimals: int = 1) -> str:
    if value is None:
        return "Tidak tersedia"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "Tidak tersedia"
    if pd.isna(number):
        return "Tidak tersedia"
    return f"{number:.{decimals}f}%".replace(".", ",")


def delta_text(value: Any, unit: str = "prestasi") -> str:
    if value is None:
        return f"Tidak tersedia ({unit})"
    try:
        number = int(value)
    except (TypeError, ValueError):
        return f"Tidak tersedia ({unit})"
    if number > 0:
        return f"+{format_number(number)} {unit}"
    return f"{format_number(number)} {unit}"


def ratio_text(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if pd.isna(number):
        return "-"
    return f"{number:.{decimals}f}".replace(".", ",")


def show_no_data(message: str = "Tidak ada data yang sesuai dengan filter.") -> None:
    st.info(message)


def ranking_table(
    frame: pd.DataFrame,
    labels: Dict[str, str],
    height: int = 420,
    empty_message: str = "Tidak ada data peringkat.",
) -> None:
    table_block(frame, labels=labels, height=height, empty_message=empty_message)


def section_header(title: str, caption: Optional[str] = None) -> None:
    section_title(title, caption)
