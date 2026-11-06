from __future__ import annotations

import html
from typing import Any, Iterable, Optional

import streamlit as st

from config import settings
from modules.data_normalizer import is_valid_url
from modules.date_helper import format_date_id


def load_css() -> None:
    if settings.STYLE_FILE.exists():
        st.markdown(
            f"<style>{settings.STYLE_FILE.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="main-header">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, caption: Optional[str] = None) -> None:
    markup = f'<div class="sapm-section-title">{html.escape(title)}</div>'
    if caption:
        markup += f'<div class="sapm-muted">{html.escape(caption)}</div>'
    st.markdown(markup, unsafe_allow_html=True)


def empty_state(title: str, message: str) -> None:
    st.markdown(f"### {html.escape(title)}")
    st.info(message)


def missing_data_notice() -> None:
    if settings.PUBLIC_READ_ONLY:
        st.info("Belum ada data prestasi yang tersedia.")
    else:
        st.info("Belum ada data prestasi. Buka menu Impor Data untuk mengunggah file Excel atau CSV.")


def render_links(label: str, url: Optional[str], key: str) -> None:
    if url and is_valid_url(url):
        st.link_button(label, url, width="stretch", key=key)
    else:
        st.caption(f"{label}: tidak tersedia")


def detail_card(title: str, items: Iterable[tuple[str, Any]]) -> None:
    rows = []
    for label, value in items:
        if value is None:
            value = "-"
        if hasattr(value, "isoformat") and not isinstance(value, str):
            value = format_date_id(value)
        rows.append(
            f"""
            <div class="detail-item">
                <span class="detail-label">{html.escape(str(label))}</span>
                <span class="detail-value">{html.escape(str(value))}</span>
            </div>
            """
        )
    st.markdown(
        f"""
        <div class="detail-card">
            <h3>{html.escape(title)}</h3>
            <div class="detail-grid">{''.join(rows)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_number(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return "0"
    return f"{number:,}".replace(",", ".")


def status_badge(status: str) -> str:
    normalized = (status or "").lower()
    if normalized in {"berhasil", "selesai"}:
        css = "sapm-badge-success"
    elif normalized in {"sebagian", "tanpa_perubahan", "proses"}:
        css = "sapm-badge-warning"
    else:
        css = "sapm-badge-danger"
    label = normalized.replace("_", " ").title() if normalized else "-"
    return f'<span class="sapm-badge {css}">{html.escape(label)}</span>'
