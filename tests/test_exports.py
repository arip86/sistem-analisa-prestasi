from __future__ import annotations

import io

from openpyxl import load_workbook

from config import settings
from config.constants import CATEGORY_LABELS, LEVEL_LABELS, PERINGKAT_LABELS
from modules.analytics import category_summary, student_ranking
from modules.data_loader import load_source_path
from modules.data_normalizer import normalize_dataframe
from modules.excel_export import build_data_excel, build_report_excel
from modules.pdf_export import build_report_pdf


def _frame():
    loaded = load_source_path(settings.EXCEL_SOURCE_FILE)
    frame = normalize_dataframe(loaded.frame).head(5).copy()
    frame["prestasi_id"] = range(1, len(frame) + 1)
    frame["kategori_kode"] = frame["kategori"]
    frame["kategori_nama"] = frame["kategori"].map(lambda code: CATEGORY_LABELS.get(code, code))
    frame["level_label"] = frame["level"].map(lambda code: LEVEL_LABELS.get(code, code))
    frame["peringkat_label"] = frame["peringkat"].map(lambda code: PERINGKAT_LABELS.get(code, code))
    frame["tahun"] = frame["tgl_sertifikat"].map(lambda value: value.year if value else None)
    frame["is_duplicate_suspect"] = False
    frame["bulan"] = frame["tgl_sertifikat"].map(lambda value: value.month if value else None)
    return frame


def test_data_excel_export():
    content = build_data_excel(_frame())
    assert content[:2] == b"PK"
    workbook = load_workbook(io.BytesIO(content), read_only=True)
    assert "Data Prestasi" in workbook.sheetnames
    header = [cell.value for cell in next(workbook["Data Prestasi"].iter_rows(min_row=1, max_row=1))]
    assert "NIM" in header
    assert "Nama Mahasiswa" in header


def test_report_excel_export_has_sheets():
    content = build_report_excel(_frame())
    workbook = load_workbook(io.BytesIO(content), read_only=True)
    for sheet in [
        "Rekap",
        "Data Prestasi",
        "Per Kategori",
        "Per Level",
        "Per Peringkat",
        "Per Tahun",
        "Ranking Mahasiswa",
        "Ranking Dosen",
    ]:
        assert sheet in workbook.sheetnames


def test_pdf_export():
    frame = _frame()
    content = build_report_pdf(
        title="Laporan Prestasi Mahasiswa",
        subtitle="Sistem Analisis Prestasi Mahasiswa (SAPM)",
        summary_rows=[("Total prestasi", len(frame))],
        sections=[
            {"title": "Rekap Kategori", "frame": category_summary(frame)},
            {"title": "Ranking Mahasiswa", "frame": student_ranking(frame)},
        ],
    )
    assert content[:5] == b"%PDF-"
    assert len(content) > 1000
