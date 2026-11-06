from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect

from config import settings
from database.connection import (
    check_connection,
    create_schema_if_needed,
    get_engine,
    masked_database_info,
)
from database.models import Base
from database.repositories import fetch_existing_fingerprints
from modules.anonymizer import anonymize_dataframe
from modules.data_loader import load_source_path
from modules.data_normalizer import normalize_dataframe
from modules.data_validator import validate_dataframe
from modules.import_service import generate_file_hash, import_valid_dataframe


def initialize_schema() -> None:
    create_schema_if_needed()
    engine = get_engine()
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    schema = settings.DB_SCHEMA or None
    tables = sorted(inspector.get_table_names(schema=schema))
    print(f"Database: {masked_database_info()}")
    print(f"Schema: {settings.DB_SCHEMA}")
    print(f"Tabel: {', '.join(tables)}")


def import_excel(path: Path, public: bool = False) -> None:
    if not path.exists():
        raise SystemExit(f"File tidak ditemukan: {path}")
    content = path.read_bytes()
    loaded = load_source_path(path)
    normalized = normalize_dataframe(loaded.frame)
    nama_file = path.name
    sheet_name = loaded.sheet_name
    if public:
        if not settings.ANONYMIZATION_SALT:
            raise SystemExit("ANONYMIZATION_SALT wajib diisi untuk import data publik.")
        normalized = anonymize_dataframe(normalized, settings.ANONYMIZATION_SALT)
        nama_file = "dataset_publik_anonim.xlsx"
        sheet_name = "Data Publik"
        content = normalized.to_csv(index=False).encode("utf-8")
    existing = fetch_existing_fingerprints()
    validation = validate_dataframe(normalized, existing)
    print(f"File: {nama_file} | Sheet: {sheet_name}")
    print(f"Mode: {'publik (anonim)' if public else 'lokal (data asli)'}")
    print(f"Total baris: {validation.total_rows}")
    print(f"Valid: {validation.valid_rows}")
    print(f"Tidak valid: {validation.invalid_rows}")
    print(f"Duplikat database: {validation.existing_duplicates}")
    print(f"Duplikat potensial: {validation.duplicate_suspects}")
    for warning in validation.warnings:
        print(f"Peringatan: {warning}")
    if validation.valid.empty:
        if validation.existing_duplicates:
            print("Semua baris sudah ada di database. Tidak ada perubahan.")
            return
        detail = ""
        if not validation.invalid.empty:
            sample = validation.invalid.head(5)
            detail = "\n" + sample[["source_row_number", "validation_errors"]].to_string(index=False)
        raise SystemExit(f"Tidak ada baris valid untuk diimpor.{detail}")
    result = import_valid_dataframe(
        valid=validation.valid,
        nama_file=nama_file,
        file_hash=generate_file_hash(content),
        sheet_name=sheet_name,
        total_rows=validation.total_rows,
        invalid_rows=validation.invalid_rows,
        existing_duplicates=validation.existing_duplicates,
        duplicate_suspects=validation.duplicate_suspects,
    )
    print(
        "Import selesai: "
        f"{result['berhasil']} berhasil, "
        f"{result['gagal']} gagal, "
        f"{result['duplikat']} duplikat, "
        f"{result['potensi_duplikat']} potensi duplikat."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Inisialisasi database SAPM dan impor data Excel.")
    parser.add_argument("--import", dest="import_file", action="store_true", help="Impor file Excel setelah tabel dibuat.")
    parser.add_argument("--public", action="store_true", help="Anonimkan data sebelum impor untuk aplikasi publik.")
    parser.add_argument("--file", dest="file_path", default=str(settings.EXCEL_SOURCE_FILE), help="Path file Excel/CSV.")
    args = parser.parse_args()

    if not settings.is_configured():
        raise SystemExit("DATABASE_URL belum dikonfigurasi. Salin .env.example menjadi .env.")
    if not check_connection():
        raise SystemExit("Koneksi database gagal. Periksa DATABASE_URL dan server PostgreSQL.")

    initialize_schema()
    if args.import_file:
        import_excel(Path(args.file_path), public=args.public)


if __name__ == "__main__":
    main()
