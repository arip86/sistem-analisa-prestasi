from __future__ import annotations

import html
from typing import Any

import streamlit as st

from config.constants import ACCENT_COLOR


def kpi_card(title: str, value: Any, subtitle: str = "", color: str = ACCENT_COLOR) -> None:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left-color: {html.escape(color)};">
            <div class="kpi-title">{html.escape(str(title))}</div>
            <div class="kpi-value">{html.escape(str(value))}</div>
            <div class="kpi-sub">{html.escape(str(subtitle))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_grid(items: list[dict], columns: int = 4) -> None:
    if not items:
        return
    for start in range(0, len(items), columns):
        row = st.columns(min(columns, len(items) - start))
        for column, item in zip(row, items[start : start + columns]):
            with column:
                kpi_card(
                    item.get("title", ""),
                    item.get("value", ""),
                    item.get("subtitle", ""),
                    item.get("color", ACCENT_COLOR),
                )


def highlight_card(
    label: str,
    value: str,
    meta: str = "",
    color: str = ACCENT_COLOR,
) -> None:
    st.markdown(
        f"""
        <div class="highlight-card" style="--highlight-color: {html.escape(color)};">
            <div class="highlight-label">{html.escape(str(label))}</div>
            <div class="highlight-value">{html.escape(str(value))}</div>
            <div class="highlight-meta">{html.escape(str(meta))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_highlight_grid(items: list[dict], columns: int = 4) -> None:
    if not items:
        return
    row = st.columns(min(columns, len(items)))
    for column, item in zip(row, items):
        with column:
            highlight_card(
                item.get("label", ""),
                item.get("value", ""),
                item.get("meta", ""),
                item.get("color", ACCENT_COLOR),
            )
