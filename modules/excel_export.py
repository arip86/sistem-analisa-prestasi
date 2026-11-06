from __future__ import annotations

import io
from datetime import date, datetime

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from config.constants import CATEGORY_LABELS
from modules.analytics import (
    category_summary,
    dosen_ranking,
    level_counts,
    peringkat_counts,
    recap_dataframe,
    student_ranking,
    year_counts,
)

NAVY = "0B1F3A"
BLUE = "1E4E8C"
LIGHT_BLUE = "EAF2FB"
WHITE = "FFFFFF"


def _excel_safe(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    for column in data.columns:
        values = []
        for value in data[column].tolist():
            if value is None:
                values.append(None)
                continue
            try:
                if pd.isna(value):
                    values.append(None)
                    continue
            except (TypeError, ValueError):
                pass
            if isinstance(value, pd.Timestamp):
                values.append(value.date())
            elif isinstance(value, datetime):
                values.append(value.date())
            elif isinstance(value, date):
                values.append(value)
            else:
                values.append(value)
        data[column] = values
    return data.astype(object).where(pd.notna(data), None)


def prestasi_display_df(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "No",
                "NIM",
                "Nama Mahasiswa",
                "Kategori",
                "Kode Kategori",
                "Level",
                "Lomba",
                "Cabang",
                "Penyelenggara",
                "Peringkat",
                "Tanggal Sertifikat",
                "Tahun",
                "Jumlah Peserta",
                "Kelompok",
                "Bentuk",
                "Keterangan",
                "Dosen Pendamping",
                "NUPTK Dosen",
                "Link Peserta",
                "Link Sertifikat",
                "Link Foto",
                "Link Dokumen Undangan",
                "Link Surat Tugas",
                "Sumber Baris",
                "Duplikat Potensial",
            ]
        )
    data = frame.copy()
    data = data.sort_values(["tgl_sertifikat", "prestasi_id"], ascending=[False, False])
    rows = []
    for index, (_, row) in enumerate(data.iterrows(), start=1):
        kode = row.get("kategori_kode")
        rows.append(
            {
                "No": index,
                "NIM": row.get("mahasiswa_nim"),
                "Nama Mahasiswa": row.get("mahasiswa_nama"),
                "Kategori": CATEGORY_LABELS.get(kode, row.get("kategori_nama") or kode),
                "Kode Kategori": kode,
                "Level": row.get("level_label"),
                "Lomba": row.get("lomba"),
                "Cabang": row.get("cabang"),
                "Penyelenggara": row.get("penyelenggara"),
                "Peringkat": row.get("peringkat_label"),
                "Tanggal Sertifikat": row.get("tgl_sertifikat"),
                "Tahun": row.get("tahun"),
                "Jumlah Peserta": row.get("jumlah_unit_peserta"),
                "Kelompok": row.get("kelompok_prestasi"),
                "Bentuk": row.get("bentuk"),
                "Keterangan": row.get("keterangan"),
                "Dosen Pendamping": row.get("dosen_nama"),
                "NUPTK Dosen": row.get("dosen_nuptk"),
                "Link Peserta": row.get("url_peserta"),
                "Link Sertifikat": row.get("url_sertifikat"),
                "Link Foto": row.get("url_foto_upp"),
                "Link Dokumen Undangan": row.get("url_dokumen_undangan"),
                "Link Surat Tugas": row.get("dosen_url_surat_tugas"),
                "Sumber Baris": row.get("source_row_number"),
                "Duplikat Potensial": "Ya" if row.get("is_duplicate_suspect") else "Tidak",
            }
        )
    return pd.DataFrame(rows)


def _style_sheet(worksheet, header_row: int = 1, max_width: int = 50) -> None:
    header_fill = PatternFill("solid", fgColor=NAVY)
    header_font = Font(color=WHITE, bold=True, size=10)
    thin_border = Border(
        left=Side(style="thin", color="D9E2EC"),
        right=Side(style="thin", color="D9E2EC"),
        top=Side(style="thin", color="D9E2EC"),
        bottom=Side(style="thin", color="D9E2EC"),
    )
    for cell in worksheet[header_row]:
        if cell.value is not None:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
    worksheet.freeze_panes = worksheet.cell(row=header_row + 1, column=1)
    if worksheet.max_row > header_row:
        worksheet.auto_filter.ref = (
            f"A{header_row}:{get_column_letter(worksheet.max_column)}{worksheet.max_row}"
        )
    for column_index in range(1, worksheet.max_column + 1):
        letter = get_column_letter(column_index)
        max_length = 0
        for cell in worksheet[letter]:
            value = "" if cell.value is None else str(cell.value)
            if len(value) > max_length:
                max_length = len(value)
        worksheet.column_dimensions[letter].width = min(max(10, max_length + 2), max_width)


def _write_frame(writer: pd.ExcelWriter, sheet_name: str, frame: pd.DataFrame) -> None:
    safe = _excel_safe(frame)
    safe.to_excel(writer, sheet_name=sheet_name, index=False)
    _style_sheet(writer.sheets[sheet_name])


def _write_summary(writer: pd.ExcelWriter, frame: pd.DataFrame) -> None:
    workbook = writer.book
    worksheet = workbook.create_sheet("Rekap", 0)
    metrics = recap_dataframe(frame)
    metadata = pd.DataFrame(
        [
            ("Aplikasi", "Sistem Analisis Prestasi Mahasiswa (SAPM)"),
            ("Dibuat", datetime.now().strftime("%d-%m-%Y %H:%M")),
            ("Total baris data", len(frame)),
        ],
        columns=["Metrik", "Nilai"],
    )
    combined = pd.concat([metadata, pd.DataFrame([("", "")], columns=["Metrik", "Nilai"]), metrics], ignore_index=True)
    for row_index, row in enumerate(combined.itertuples(index=False), start=1):
        worksheet.cell(row=row_index, column=1, value=row[0])
        worksheet.cell(row=row_index, column=2, value=row[1])
    worksheet.column_dimensions["A"].width = 32
    worksheet.column_dimensions["B"].width = 45
    for cell in worksheet[1]:
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(color=WHITE, bold=True)
    worksheet.freeze_panes = "A2"


def build_report_excel(frame: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _write_summary(writer, frame)
        _write_frame(writer, "Data Prestasi", prestasi_display_df(frame))
        _write_frame(writer, "Per Kategori", category_summary(frame))
        _write_frame(writer, "Per Level", level_counts(frame))
        _write_frame(writer, "Per Peringkat", peringkat_counts(frame))
        _write_frame(writer, "Per Tahun", year_counts(frame))
        _write_frame(writer, "Ranking Mahasiswa", student_ranking(frame))
        _write_frame(writer, "Ranking Dosen", dosen_ranking(frame))
    output.seek(0)
    return output.getvalue()


def build_data_excel(frame: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _write_frame(writer, "Data Prestasi", prestasi_display_df(frame))
    output.seek(0)
    return output.getvalue()
