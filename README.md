# Aplikasi Uji Emisi

Aplikasi web untuk mengelola dan mencatat hasil uji emisi kendaraan. Aplikasi ini memungkinkan pengguna untuk mencatat data kendaraan, melakukan uji emisi, dan melihat hasil uji dalam bentuk tabel serta mengekspor data ke format CSV dan Excel.

## Daftar Isi
- [Aplikasi Uji Emisi](#aplikasi-uji-emisi)
  - [Daftar Isi](#daftar-isi)
  - [Ringkasan](#ringkasan)
  - [Fitur](#fitur)
  - [Teknologi yang Digunakan](#teknologi-yang-digunakan)
  - [Persyaratan Sistem](#persyaratan-sistem)
  - [Instalasi](#instalasi)
    - [Menggunakan Git](#menggunakan-git)
    - [Manual Setup](#manual-setup)
    - [Konfigurasi Database](#konfigurasi-database)
  - [Menjalankan Aplikasi](#menjalankan-aplikasi)
    - [Development Mode](#development-mode)
    - [Production Mode](#production-mode)
  - [Struktur Aplikasi](#struktur-aplikasi)
  - [Modul dan Komponen](#modul-dan-komponen)
    - [Blueprints](#blueprints)
    - [Models](#models)
    - [Routes](#routes)
  - [User Interface](#user-interface)
    - [Halaman Kendaraan](#halaman-kendaraan)
    - [Halaman Uji Emisi](#halaman-uji-emisi)
    - [Halaman Laporan](#halaman-laporan)
    - [Halaman User Management](#halaman-user-management)
    - [Halaman Konfigurasi](#halaman-konfigurasi)
  - [Penggunaan](#penggunaan)
    - [Manajemen Data Kendaraan](#manajemen-data-kendaraan)
    - [Proses Uji Emisi](#proses-uji-emisi)
    - [Melihat dan Filter Hasil](#melihat-dan-filter-hasil)
    - [Export Data](#export-data)
    - [Manajemen User](#manajemen-user)
  - [API Reference](#api-reference)
  - [Troubleshooting](#troubleshooting)
  - [Keamanan](#keamanan)
  - [Pengembangan](#pengembangan)
    - [Panduan Kontribusi](#panduan-kontribusi)
    - [Coding Standards](#coding-standards)
  - [Changelog](#changelog)
  - [Lisensi](#lisensi)
  - [Kontak](#kontak)

## Ringkasan

Aplikasi Uji Emisi adalah solusi web-based untuk mengelola dan mencatat proses uji emisi kendaraan bermotor. Aplikasi ini dibangun untuk mempermudah petugas uji emisi dalam mencatat, mengevaluasi, dan menghasilkan laporan hasil uji emisi secara efisien. Sistem secara otomatis memvalidasi hasil uji berdasarkan standar yang telah ditetapkan dan mengategorikan kendaraan sebagai "Lulus" atau "Tidak Lulus".

## Fitur

- ✨ **Input Data Kendaraan**
  - Formulir input kendaraan dengan validasi real-time
  - Klasifikasi kendaraan (umum/dinas)
  - Pencatatan detail kendaraan (plat nomor, merek, tipe, tahun)
  - Pemilihan jenis bahan bakar (bensin/solar)
  - Kategori beban berdasarkan jenis bahan bakar
  - Input batch kendaraan via CSV

- 📊 **Uji Emisi**
  - Interface input hasil uji untuk kendaraan terdaftar
  - Parameter berbeda untuk kendaraan bensin dan solar
  - Input parameter uji (CO, CO2, HC, O2, Lambda untuk bensin)
  - Input Opasitas untuk kendaraan solar

- 📈 **Analisis dan Laporan**
  - Validasi otomatis berdasarkan standar emisi
  - Dashboard dengan statistik hasil uji
  - Filtering dan pencarian data multi-parameter
  - Pagination untuk set data besar
  - Export ke format CSV dan Excel

- 👥 **Manajemen User**
  - Sistem login dengan level akses berbeda (Admin, Operator)
  - Pencatatan user yang melakukan uji emisi
  - Pelacakan aktivitas user

- 🛠️ **Konfigurasi Sistem**
  - Pengaturan standar batas emisi per kategori
  - Kustomisasi parameter aplikasi

- 📱 **User Experience**
  - Responsive design adaptif untuk desktop dan mobile
  - Tema modern dengan Tailwind CSS
  - Notifikasi toast untuk feedback aksi user
  - Loading indicators
  - Form validation

## Teknologi yang Digunakan

- **Backend**:
  - Python 3.8+ dengan Flask 2.x framework
  - RESTful API dengan JSON responses
  - Flask extensions:
    - Flask-SQLAlchemy (ORM)
    - Flask-Migrate (database migrations)
    - Flask-Login (user authentication)
    - Flask-WTF (forms & validation)
    - Flask-Limiter (rate limiting)
    - Flask-CORS (cross-origin resource sharing)

- **Database**:
  - SQLite untuk development
  - Migrasi database dengan Alembic
  - Struktur relasional untuk kendaraan, hasil uji, dan users

- **Frontend**:
  - HTML5 + CSS3 + JavaScript (ES6+)
  - Tailwind CSS 3.x untuk styling responsif
  - Font Awesome 6.x untuk icons
  - Modular JavaScript dengan file terpisah per halaman
  - Notifikasi toast system terpusat

- **Keamanan**:
  - Password hashing
  - CSRF protection
  - Input sanitization
  - Rate limiting untuk API endpoints
  - Content Security Policy

- **Development Tools**:
  - Git untuk version control
  - Virtual environment untuk isolasi dependency

## Persyaratan Sistem

- **Software**:
  - Python 3.8 atau lebih baru
  - pip (Python package installer)
  - Web browser modern (Chrome, Firefox, Safari, Edge)
  - Git (opsional, untuk cloning)

- **Hardware**:
  - Minimum: 1GB RAM, 1GHz CPU, 500MB disk space
  - Rekomendasi: 2GB+ RAM, 2GHz+ CPU, 1GB+ disk space

- **Sistem operasi**:
  - Windows 10/11
  - Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
  - macOS 10.15+

## Instalasi

### Menggunakan Git

1. Clone repository:
   ```bash
   git clone https://github.com/khimawan/Web-app-Uji-Emisi-Count.git
   cd Web-app-Uji-Emisi-Count
   ```

2. Buat virtual environment:
   ```bash
   # Di Windows
   python -m venv .venv
   
   # Di Linux/MacOS
   python3 -m venv .venv
   ```

3. Aktifkan virtual environment:
   ```bash
   # Di Windows
   .venv\Scripts\activate
   
   # Di Linux/MacOS
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Manual Setup

1. Download file ZIP dari repository GitHub
2. Extract file ke folder pilihan
3. Buka command prompt/terminal di folder tersebut
4. Ikuti langkah 2-4 dari "Menggunakan Git"

### Konfigurasi Database

1. Inisialisasi database:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

2. (Opsional) Buat user admin:
   ```bash
   python migrations.py
   ```

## Menjalankan Aplikasi

### Development Mode

1. Pastikan virtual environment sudah aktif:
   ```bash
   # Di Windows
   .venv\Scripts\activate
   
   # Di Linux/MacOS
   source .venv/bin/activate
   ```

2. Jalankan aplikasi dalam mode development:
   ```bash
   python main.py
   ```

3. Buka browser dan akses:
   ```
   http://localhost:5000
   ```

### Production Mode

1. Set environment variable:
   ```bash
   # Di Windows
   set FLASK_ENV=production
   
   # Di Linux/MacOS
   export FLASK_ENV=production
   ```

2. Jalankan dengan Gunicorn (Disarankan untuk production):
   ```bash
   gunicorn -w 4 "wsgi:create_app()"
   ```

3. Alternatif bisa menggunakan supervisor atau systemd untuk menjaga aplikasi tetap berjalan

## Struktur Aplikasi

```
Web-app-Uji-Emisi-Count/
├── blueprints/                # Blueprint modules untuk routes
│   ├── __init__.py
│   ├── auth.py                # Authentication routes
│   ├── vehicles.py            # Vehicle management
│   ├── tests.py               # Emission test routes
│   ├── reports.py             # Reporting routes
│   └── api.py                 # API endpoints
├── instance/                  # Instance-specific files
│   └── emisi.db               # SQLite database file
├── migrations/                # Database migration files
│   └── ...
├── static/                    # Static files
│   ├── css/                   # CSS styles
│   ├── js/                    # JavaScript files
│   │   ├── halaman1.js        # Scripts for kendaraan
│   │   ├── halaman2.js        # Scripts for uji emisi
│   │   ├── halaman3.js        # Scripts for reports
│   │   ├── users.js           # Scripts for user management  
│   │   └── toast.js           # Notification system
│   └── images/                # Image assets
├── templates/                 # HTML templates
│   ├── base.html              # Base template with layout
│   ├── halaman1.html          # Kendaraan input form
│   ├── halaman2.html          # Uji emisi page
│   ├── halaman3.html          # Reports page
│   ├── users.html             # User management
│   ├── config.html            # Configuration page
│   ├── login.html             # Login page
│   └── error.html             # Error pages
├── .gitignore                 # Git ignore file
├── app_init.py                # Application initialization
├── evaluate.py                # Emission evaluation logic
├── extensions.py              # Flask extensions setup
├── main.py                    # Development entry point
├── migrate_fuel_types.py      # Migration script
├── migrations.py              # Database migration control
├── models.py                  # Database models
├── requirements.txt           # Python dependencies
├── routes.py                  # Main routes setup
├── test_db.py                 # Database testing script
├── wsgi.py                    # WSGI entry point for production
├── LICENSE                    # License file
└── README.md                  # This documentation file
```

## Modul dan Komponen

### Blueprints

Aplikasi diorganisir dalam Flask blueprints untuk modularitas:

- **auth**: Manajemen autentikasi dan user
- **vehicles**: Manajemen data kendaraan
- **tests**: Proses uji emisi
- **reports**: Laporan dan export data
- **api**: API endpoints untuk operasi CRUD

### Models

Database models yang didefinisikan di `models.py`:

- **User**: Informasi user dan autentikasi
- **Kendaraan**: Data kendaraan
- **HasilUji**: Hasil pengujian emisi
- **Config**: Konfigurasi sistem

### Routes

Routes utama didefinisikan di modul masing-masing:

- **Authentication**: Login, logout, user management
- **Vehicle Management**: CRUD untuk kendaraan, batch upload
- **Emission Tests**: Input dan evaluasi hasil uji
- **Reporting**: Melihat hasil, filter, dan export data

## User Interface

### Halaman Kendaraan

- Form input data kendaraan
- Upload batch via CSV
- Validasi data real-time

### Halaman Uji Emisi

- Daftar kendaraan yang terdaftar
- Filter dan pencarian kendaraan
- Form input hasil uji emisi dengan validasi
- Perbedaan form untuk kendaraan bensin dan solar

### Halaman Laporan

- Tabel hasil uji emisi
- Filter multi-parameter (tanggal, plat nomor, merek, hasil uji)
- Pagination untuk navigasi data
- Export ke CSV dan Excel

### Halaman User Management

- Daftar user
- Form tambah/edit user
- Pengaturan role dan permission

### Halaman Konfigurasi

- Pengaturan standar emisi
- Konfigurasi aplikasi

## Penggunaan

### Manajemen Data Kendaraan

1. **Input Manual**:
   - Buka halaman "Input Data Kendaraan"
   - Isi formulir dengan data lengkap
   - Pilih jenis kendaraan (umum/dinas)
   - Pilih bahan bakar (bensin/solar)
   - Pilih kategori beban sesuai jenis bahan bakar
   - Kendaraan dinas memerlukan input nama instansi
   - Klik "Simpan Data"

2. **Input Batch**:
   - Download template CSV dari aplikasi
   - Isi data kendaraan sesuai format
   - Upload CSV melalui form batch upload
   - Sistem akan menampilkan hasil upload (sukses/error)

### Proses Uji Emisi

1. **Mencari Kendaraan**:
   - Buka halaman "Daftar Kendaraan"
   - Cari kendaraan dengan filter (plat nomor, merek, dll)
   - Klik tombol uji pada kendaraan yang dipilih

2. **Input Hasil Uji**:
   - Untuk kendaraan bensin: isi nilai CO, CO2, HC, O2, Lambda
   - Untuk kendaraan solar: isi nilai Opasitas
   - Klik "Simpan Hasil"
   - Sistem akan mengevaluasi hasil sesuai standar

3. **Melihat Status**:
   - Hasil evaluasi akan muncul otomatis
   - Kendaraan akan terlabel "Valid/Tidak Valid" dan "Lulus/Tidak Lulus"

### Melihat dan Filter Hasil

1. **Laporan Umum**:
   - Buka halaman "Data Kendaraan dan Hasil Uji"
   - Lihat statistik dan data dalam tabel

2. **Filtering**:
   - Gunakan form filter untuk menyaring data
   - Filter berdasarkan plat nomor, merek, rentang tanggal, hasil uji
   - Hasil filter akan diupdate secara dinamis

3. **Navigasi Data**:
   - Gunakan pagination untuk melihat halaman selanjutnya
   - Jumlah hasil dan halaman ditampilkan

### Export Data

1. **Export ke CSV**:
   - Klik tombol "Export CSV" di halaman report
   - File akan otomatis terdownload

2. **Export ke Excel**:
   - Klik tombol "Export Excel" di halaman report
   - File Excel akan terdownload dengan formatting

3. **Format Data Export**:
   - Tanggal dan waktu uji
   - Detail kendaraan (plat, merek, tipe, dll)
   - Hasil pengukuran emisi
   - Status validasi dan kelulusan
   - Data operator yang melakukan uji

### Manajemen User

1. **Menambah User**:
   - Login sebagai administrator
   - Buka halaman "Users"
   - Klik "Add New User"
   - Isi form dengan data lengkap
   - Set role (Admin/Operator)

2. **Edit User**:
   - Klik icon edit pada user yang ingin diubah
   - Update informasi yang diperlukan
   - Password bisa dikosongkan jika tidak ingin diubah

3. **Hapus User**:
   - Klik icon delete pada user
   - Konfirmasi penghapusan

## API Reference

Aplikasi menyediakan API endpoints untuk integrasi:

- **Kendaraan**:
  - `GET /api/kendaraan-list` - List kendaraan dengan pagination
  - `POST /api/kendaraan` - Tambah kendaraan baru
  - `GET /api/kendaraan/{plat}` - Detail kendaraan
  - `DELETE /api/kendaraan/{plat}` - Hapus kendaraan
  - `POST /api/kendaraan/batch-upload` - Upload batch kendaraan

- **Hasil Uji**:
  - `POST /api/hasil-uji/{plat}` - Rekam hasil uji
  - `GET /api/hasil-uji/{plat}` - Ambil hasil uji
  - `DELETE /api/hasil-uji/{plat}` - Hapus hasil uji
  - `GET /api/hasil-uji/tested-plats` - List plat yang sudah diuji

- **Config**:
  - `GET /api/config` - Lihat konfigurasi
  - `POST /api/config` - Update konfigurasi

- **Users**:
  - `GET /api/v1/users/{id}` - Detail user

## Troubleshooting

1. **Error "No module named 'flask'"**:
   - Pastikan virtual environment aktif
   - Verifikasi dengan `pip list` untuk memeriksa packages terinstall
   - Jalankan ulang `pip install -r requirements.txt`

2. **Database Errors**:
   - Untuk kesalahan migrasi: `flask db stamp head` lalu `flask db migrate` dan `flask db upgrade`
   - Untuk reset database: hapus file `instance/emisi.db` dan jalankan kembali migrasi
   - Jika tabel tidak terbuat: pastikan `SQLALCHEMY_DATABASE_URI` benar di konfigurasi

3. **Port 5000 sudah digunakan**:
   - Cek process yang menggunakan port: `netstat -ano | findstr :5000` (Windows) atau `lsof -i:5000` (Linux/Mac)
   - Hentikan process tersebut atau
   - Ubah port di `main.py` dengan menambahkan `port=5001` di `app.run()`

4. **Login Gagal**:
   - Reset password dengan command `python reset_password.py`
   - Pastikan user dan password benar
   - Periksa log untuk error detail

5. **Form tidak berfungsi**:
   - Buka developer tools browser (F12) untuk melihat error JavaScript
   - Pastikan CSRF token terpasang di form
   - Periksa network request di developer tools

6. **Export tidak berfungsi**:
   - Periksa permission folder untuk menulis file
   - Pastikan format data valid
   - Cek error di console browser

## Keamanan

- **Authentication**:
  - Password hashing dengan Flask-Login
  - Session management yang aman
  - CSRF protection pada semua form

- **Database**:
  - Parameterized queries dengan SQLAlchemy untuk mencegah SQL injection
  - Input sanitization sebelum penyimpanan

- **Frontend**:
  - Content Security Policy untuk mencegah XSS
  - Form validation di client dan server side
  - Sanitasi output sebelum display

- **API**:
  - Rate limiting untuk mencegah brute force
  - Validasi token untuk API calls
  - Input validation untuk semua parameters

## Pengembangan

### Panduan Kontribusi

1. **Fork Repository**:
   - Buat fork dari repository utama
   - Clone fork ke lokal development environment

2. **Buat Branch**:
   - Buat branch baru untuk fitur/perbaikan: `git checkout -b feature/nama-fitur`
   - Jangan langsung commit ke branch master

3. **Development Flow**:
   - Pastikan code berfungsi dan tertest
   - Perbarui dokumentasi jika diperlukan
   - Ikuti coding standard

4. **Submit Perubahan**:
   - Buat pull request ke repository utama
   - Jelaskan perubahan dan alasan perubahan

### Coding Standards

- **Python**:
  - Ikuti PEP 8 style guide
  - Gunakan docstrings untuk dokumentasi fungsi
  - Maximum line length: 79 characters

- **JavaScript**:
  - Gunakan ES6+ features
  - Modul terpisah per halaman
  - Comment untuk fungsi kompleks

- **HTML/CSS**:
  - Konsisten menggunakan Tailwind classes
  - Semantic HTML
  - Mobile-first approach

## Changelog

- **v2.0.0** - Current version
  - Refactor komponen JavaScript ke file terpisah
  - Menambahkan sistem notifikasi terpusat (toast)
  - Perbaikan UI/UX, termasuk loading indicators
  - Export ke Excel
  - Filter dinamis di halaman reports

- **v1.0.0** - Initial release
  - Fitur dasar input kendaraan dan uji emisi
  - Export CSV
  - User authentication

## Lisensi

[MIT License](LICENSE)

## Kontak

Untuk pertanyaan, dukungan, atau kontribusi, silakan hubungi:
- GitHub Issues: https://github.com/khimawan/Web-app-Uji-Emisi-Count/issues
- Email: [YOUR_EMAIL]
