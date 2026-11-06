from __future__ import annotations

import io
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#0B1F3A")
BLUE = colors.HexColor("#1E4E8C")
LIGHT_BLUE = colors.HexColor("#EAF2FB")
GRID = colors.HexColor("#CBD5E1")
TEXT = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#475569")


def _format_cell(value: Any, max_length: int = 70) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d-%m-%Y")
    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y")
    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))
    else:
        text = str(value)
    text = " ".join(text.split())
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def _table_data(frame: pd.DataFrame, max_rows: Optional[int] = None) -> List[List[str]]:
    data = frame if max_rows is None else frame.head(max_rows)
    header = [str(column) for column in data.columns]
    rows = [[_format_cell(value) for value in row] for row in data.itertuples(index=False, name=None)]
    return [header] + rows


def _column_widths(data: List[List[str]], available_width: float) -> List[float]:
    if not data:
        return []
    column_count = len(data[0])
    weights = []
    for column_index in range(column_count):
        max_length = 0
        for row in data[:200]:
            value = row[column_index] if column_index < len(row) else ""
            max_length = max(max_length, len(str(value)))
        weights.append(min(max(max_length, 6), 38))
    total = sum(weights) or 1
    widths = [(weight / total) * available_width for weight in weights]
    minimum = 18 * mm
    return [max(width, minimum) for width in widths]


def _build_table(data: List[List[str]], available_width: float, font_size: float = 7) -> LongTable:
    widths = _column_widths(data, available_width)
    table = LongTable(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("LEADING", (0, 0), (-1, -1), font_size + 2),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.25, GRID),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def build_report_pdf(
    title: str,
    subtitle: str,
    summary_rows: List[tuple],
    sections: List[Dict[str, Any]],
    meta_lines: Optional[List[str]] = None,
) -> bytes:
    output = io.BytesIO()
    page_size = landscape(A4)
    doc = SimpleDocTemplate(
        output,
        pagesize=page_size,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
    )
    available_width = page_size[0] - doc.leftMargin - doc.rightMargin
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=MUTED,
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=BLUE,
        spaceBefore=10,
        spaceAfter=5,
    )
    note_style = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=MUTED,
        spaceAfter=6,
    )

    story: List[Any] = []
    story.append(Paragraph(escape(title), title_style))
    story.append(Paragraph(escape(subtitle), subtitle_style))
    meta_text = [
        f"Dibuat: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
    ]
    if meta_lines:
        meta_text.extend(meta_lines)
    story.append(Paragraph(escape(" | ".join(meta_text)), subtitle_style))
    story.append(Spacer(1, 4))

    if summary_rows:
        summary_data = [["Metrik", "Nilai"]] + [[str(label), str(value)] for label, value in summary_rows]
        summary_table = Table(summary_data, colWidths=[80 * mm, 100 * mm], hAlign="LEFT")
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("GRID", (0, 0), (-1, -1), 0.25, GRID),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(summary_table)

    for section in sections:
        frame = section.get("frame")
        if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
            continue
        story.append(Paragraph(escape(str(section.get("title", "Bagian"))), section_style))
        note = section.get("note")
        if note:
            story.append(Paragraph(escape(str(note)), note_style))
        data = _table_data(frame, section.get("max_rows"))
        if len(data) > 1:
            story.append(_build_table(data, available_width, font_size=float(section.get("font_size", 7))))
        story.append(Spacer(1, 5))

    def add_page_number(canvas, document):
        page_number = canvas.getPageNumber()
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(doc.leftMargin, 8 * mm, "SAPM - Sistem Analisis Prestasi Mahasiswa")
        canvas.drawRightString(page_size[0] - doc.rightMargin, 8 * mm, f"Halaman {page_number}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    output.seek(0)
    return output.getvalue()
