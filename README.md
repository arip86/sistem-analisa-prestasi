# SAPM - Sistem Analisis Prestasi Mahasiswa

Aplikasi Streamlit untuk mengimpor, memvalidasi, mengeksplorasi, menganalisis, dan melaporkan data prestasi mahasiswa. Data disimpan di PostgreSQL dan dibaca oleh seluruh halaman aplikasi.

## Fitur

- Dasbor ringkasan: kartu capaian, sorotan mahasiswa/dosen/kategori/level, sebaran kategori dan level, tren bulanan, peringkat mahasiswa, peringkat, dan prestasi terbaru.
- Data Prestasi: pencarian, filter, tabel detail, tautan dokumen, dan unduhan Excel/CSV.
- Analisis Data: enam bagian analisis dalam satu halaman:
  - Capaian: rekap kategori, level, peringkat, matriks kategori-level, tren level per tahun, dan insight otomatis.
  - Tren Waktu: tren tahunan/bulanan, pertumbuhan, perbandingan dua periode, dan pola musiman per tahun.
  - Mahasiswa: ranking jumlah prestasi/poin, konsistensi, distribusi prestasi, komposisi individu/kelompok, dan prestasi internasional.
  - Dosen: ranking dosen, jumlah mahasiswa dampingan, serta sebaran level dan kategori.
  - Kompetisi: peringkat edisi lomba, rekap level, penyelenggara, cabang, dan kompetisi berulang.
  - Kualitas Data: kelengkapan field, validitas NIM/NUPTK, dokumen pendukung, duplikat potensial, dan field opsional kosong.
- Laporan: pratinjau laporan serta unduhan Excel dan PDF sesuai filter aktif.
- Impor Data: unggah Excel/CSV, deteksi header otomatis, validasi baris, deteksi duplikat, dan riwayat import.
- Normalisasi data: spasi berlebih, kode level/peringkat, URL, tanggal, angka, NIM, dan NUPTK.
- Duplikat potensial tetap diimpor dan ditandai untuk verifikasi manual.

## Struktur Proyek

```text
app.py                  Titik masuk Streamlit dan navigasi
config/                 Konfigurasi aplikasi dan konstanta
database/               Koneksi, model SQLAlchemy, dan repository
modules/                Loader, cleaner, normalizer, validator, analytics, import, export
modules/analysis/       Modul analisis reusable per topik (capaian, tren, mahasiswa, dosen, kompetisi, kualitas)
components/             Komponen UI, chart, filter, dan akses data ter-cache
views/                  Halaman fitur
views/analysis_sections Renderer UI untuk enam tab Analisis Data
scripts/init_db.py      Inisialisasi schema/tabel dan impor awal
assets/style.css        Gaya antarmuka
tests/                  Unit test dan smoke test database
2025-1.xlsx             File sumber data asli (tidak diubah)
```

## Prasyarat

- Python 3.10 atau lebih baru
- PostgreSQL yang dapat diakses
- File `.env` berisi konfigurasi database

## Instalasi

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Sesuaikan `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:55432/sapm
DB_SCHEMA=prestasi
APP_ENV=development
MAX_UPLOAD_MB=25
```

Jangan commit `.env` karena berisi kredensial.

## Inisialisasi Database

Membuat schema dan tabel:

```bash
python scripts/init_db.py
```

Membuat tabel sekaligus mengimpor file sumber `2025-1.xlsx`:

```bash
python scripts/init_db.py --import
```

Impor file lain:

```bash
python scripts/init_db.py --import --file path/ke/file.xlsx
```

Impor ulang file yang sama aman dilakukan. Baris dengan fingerprint yang sudah ada akan dilewati.

## Menjalankan Aplikasi

```bash
streamlit run app.py
```

Buka URL yang ditampilkan Streamlit, biasanya `http://localhost:8501`.

## Deploy ke Streamlit Community Cloud (Publik Read-Only)

Bagian ini menjelaskan deploy aplikasi publik yang hanya dapat membaca data anonim. Aplikasi menggunakan Streamlit Community Cloud dan PostgreSQL Neon. Data asli tidak boleh diimpor ke aplikasi publik.

### Prasyarat

- Repository GitHub berisi kode aplikasi.
- Database PostgreSQL Neon.
- Dua kredensial database:
  - Admin/owner untuk inisialisasi schema dan impor data.
  - User read-only untuk aplikasi yang berjalan di Streamlit Cloud.
- File `2025-1.xlsx` tersedia secara lokal untuk proses impor awal.

### 1. Inisialisasi Schema dan Impor Data Anonim

Jalankan dari folder project lokal. Gunakan kredensial admin Neon, bukan kredensial read-only.

```bash
export DATABASE_URL="postgresql+psycopg2://ADMIN:PASSWORD@HOST/neondb?sslmode=require"
export DB_SCHEMA="prestasi"
export ANONYMIZATION_SALT="string-acak-panjang-dan-tetap"

python scripts/init_db.py --import --public --file 2025-1.xlsx
```

Perintah tersebut membuat schema/tabel, menganonimkan NIM, NUPTK, nama mahasiswa, nama dosen, URL, dan keterangan, lalu menyimpan data ke database. Gunakan salt yang kuat dan jangan mengubahnya setelah impor.

Untuk mengimpor file lain:

```bash
python scripts/init_db.py --import --public --file path/ke/file.xlsx
```

### 2. Membuat User Database Read-Only

Setelah schema dan data selesai dibuat, jalankan SQL berikut melalui SQL Editor Neon. Sesuaikan `neondb` dengan nama database Anda.

```sql
CREATE ROLE sapm_reader LOGIN PASSWORD 'PASSWORD_KUAT';

GRANT CONNECT ON DATABASE neondb TO sapm_reader;
GRANT USAGE ON SCHEMA prestasi TO sapm_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA prestasi TO sapm_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA prestasi GRANT SELECT ON TABLES TO sapm_reader;
```

Aplikasi publik harus memakai `sapm_reader`, bukan user admin/owner. Dengan begitu, aplikasi tidak dapat menulis atau mengubah data meskipun menu impor tidak sengaja terbuka.

### 3. Push Repository ke GitHub

Pastikan `.env`, `.streamlit/secrets.toml`, file Excel/CSV, dan virtual environment tidak ikut ter-commit.

```bash
git init
git add .
git commit -m "Prepare Streamlit deployment"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

### 4. Mengisi Secrets Streamlit Cloud

Saat deploy, buka **Advanced settings -> Secrets**, lalu tempel konfigurasi berikut menggunakan kredensial read-only:

```toml
DATABASE_URL = "postgresql+psycopg2://sapm_reader:PASSWORD_READONLY@HOST/neondb?sslmode=require"
DB_SCHEMA = "prestasi"
APP_ENV = "production"
MAX_UPLOAD_MB = 25
PUBLIC_READ_ONLY = "true"
```

Jangan memasukkan kredensial admin Neon ke secrets aplikasi. `ANONYMIZATION_SALT` hanya diperlukan saat menjalankan `scripts/init_db.py --public` dan tidak perlu dipasang di Streamlit Cloud untuk aplikasi read-only.

### 5. Deploy

1. Buka `share.streamlit.io`.
2. Pilih **Create app** lalu **Deploy from GitHub**.
3. Pilih repository, branch `main`, dan main file `app.py`.
4. Pada **Advanced settings**, pilih Python 3.12 dan tempel secrets di atas.
5. Klik **Deploy**.

### 6. Verifikasi

- Badge database pada sidebar menunjukkan `Terhubung`.
- Jumlah prestasi, mahasiswa, dosen, dan kategori muncul.
- Menu **Impor Data** tidak tampil.
- Halaman Data Prestasi hanya menampilkan identitas yang sudah dianonimkan.
- Unduhan Excel dan PDF berfungsi.
- Tidak ada error koneksi pada log Streamlit Cloud.

### 7. Catatan Keamanan

- Jangan commit `.env` atau `.streamlit/secrets.toml`.
- `PUBLIC_READ_ONLY` hanya mengatur tampilan UI; pengaman utama adalah user database read-only.
- Impor data publik wajib menggunakan opsi `--public`.
- Simpan salt anonimisasi secara aman dan gunakan nilai yang tetap.
- Neon free tier dapat tidur saat tidak aktif, sehingga permintaan pertama bisa lebih lambat.

## Metodologi Poin

Poin prestasi = bobot level x bobot peringkat.

| Level | Bobot |
| --- | --- |
| Internasional | 5 |
| Nasional | 3 |
| Provinsi | 2 |
| Kabupaten/Kota | 1 |

| Peringkat | Bobot |
| --- | --- |
| Juara 1 | 3 |
| Juara 2 | 2 |
| Juara 3 | 1 |
| Harapan 1-3 | 1 |

Ranking utama pada Analisis Data menggunakan jumlah prestasi. Urutan mahasiswa: jumlah prestasi, poin, lalu nama. Urutan dosen: jumlah prestasi, poin, jumlah mahasiswa, lalu nama. Peringkat berbasis poin tetap tersedia melalui pilihan indikator pada tab Mahasiswa dan Dosen.

## Metodologi Analisis Data

- Jumlah prestasi dihitung dari `nunique(prestasi_id)`.
- Mahasiswa dan dosen unik dihitung setelah relasi banyak-ke-banyak dieksplode; satu prestasi dengan beberapa mahasiswa/dosen tetap dihitung satu prestasi.
- Kompetisi unik dihitung dari kombinasi `lomba` dan `tahun`.
- Tren menggunakan `tgl_sertifikat`. Periode tanpa data ditampilkan sebagai nol agar sumbu waktu tetap utuh.
- Pertumbuhan = `(periode sekarang - periode sebelumnya) / periode sebelumnya x 100`. Jika periode sebelumnya nol, nilai ditampilkan sebagai tidak tersedia.
- Konsistensi mahasiswa = jumlah bulan aktif / rentang bulan dari prestasi pertama sampai terakhir. Mahasiswa dengan satu prestasi memiliki rasio 1.
- Kualitas data dihitung pada data setelah filter. Duplikat potensial adalah penanda untuk verifikasi manual, bukan keputusan hapus otomatis.
- Tidak ada perubahan schema database untuk fitur analisis ini.

## Validasi dan Duplikat

- Kolom wajib: level, kategori, lomba, cabang, penyelenggara, peringkat, tanggal sertifikat, NIM, nama mahasiswa, NUPTK dosen, dan nama dosen.
- NIM harus berupa angka 5-20 digit. NUPTK harus 16 digit.
- Level dan peringkat harus dikenali. Tanggal harus valid. URL harus menggunakan http/https setelah normalisasi.
- Fingerprint SHA-256 mencegah penyimpanan baris identik berulang.
- Baris dengan event, mahasiswa, peringkat, dan tanggal sama tetapi dosen atau sertifikat berbeda dianggap duplikat potensial dan tetap diimpor dengan penanda.

## Pengujian

```bash
pip install -r requirements-dev.txt
pytest -q
```

Test mencakup pembersihan dan normalisasi data, validasi file sumber, perhitungan analytics lama dan baru, ekspor Excel/PDF, smoke test database, serta smoke test halaman Dasbor dan Analisis Data menggunakan Streamlit AppTest jika database siap.

## Catatan Data

- File `2025-1.xlsx` adalah sumber data riil dan tidak dimodifikasi oleh aplikasi.
- Jumlah baris saat ini: 292 prestasi, 273 mahasiswa unik, 59 dosen, 5 kategori, dan 43 kombinasi lomba-tahun.
- Delapan baris teridentifikasi sebagai duplikat potensial.
- File `.xlsx`, `.csv`, `.env`, dan direktori virtual environment tidak disertakan ke Git.
