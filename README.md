# Aplikasi Uji Emisi

Aplikasi web untuk mengelola dan mencatat hasil uji emisi kendaraan. Aplikasi ini memungkinkan pengguna untuk mencatat data kendaraan, melakukan uji emisi, dan melihat hasil uji dalam bentuk tabel serta mengekspor data ke format CSV.

## Fitur

- ✨ Input data kendaraan (plat nomor, merek, tipe, tahun)
- 📊 Input hasil uji emisi (CO, CO2, HC, O2, Lambda)
- 📈 Tampilan hasil uji dengan validasi otomatis
- 📱 Responsive design untuk desktop dan mobile
- 💾 Export data ke format CSV
- 🎨 Modern UI dengan Tailwind CSS
- 🔍 Validasi data real-time
- 📋 Notifikasi status operasi

## Teknologi yang Digunakan

- **Backend**: Python Flask
- **Database**: SQLite dengan SQLAlchemy
- **Frontend**: 
  - Tailwind CSS untuk styling
  - Font Awesome untuk icons
  - JavaScript untuk interaksi dinamis
- **Validasi**: Server-side dan client-side validation
- **Export**: CSV file generation

## Persyaratan Sistem

- Python 3.8 atau lebih baru
- pip (Python package installer)
- Web browser modern
- Sistem operasi: Windows/Linux/MacOS

## Instalasi

1. Clone repository ini:
   ```bash
   git clone <repository-url>
   cd "Web app Uji Emisi Count"
   ```

2. Buat virtual environment:
   ```bash
   # Di Windows
   python -m venv venv
   
   # Di Linux/MacOS
   python3 -m venv venv
   ```

3. Aktifkan virtual environment:
   ```bash
   # Di Windows
   venv\Scripts\activate
   
   # Di Linux/MacOS
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Menjalankan Aplikasi

1. Pastikan virtual environment sudah aktif:
   ```bash
   # Di Windows
   venv\Scripts\activate
   
   # Di Linux/MacOS
   source venv/bin/activate
   ```

2. Jalankan aplikasi:
   ```bash
   python app.py
   ```

3. Buka browser dan akses:
   ```
   http://localhost:5000
   ```

## Struktur Aplikasi

```
Web app Uji Emisi Count/
├── app.py                 # File utama aplikasi Flask
├── requirements.txt       # Daftar package yang dibutuhkan
├── emisi.db              # Database SQLite
├── static/
│   └── css/
│       └── style.css     # Custom CSS styles
└── templates/
    ├── base.html         # Template dasar
    ├── halaman1.html     # Halaman input kendaraan
    ├── halaman2.html     # Halaman input uji emisi
    ├── halaman3.html     # Halaman hasil uji
    └── error.html        # Halaman error
```

## Penggunaan

1. **Input Data Kendaraan** (Halaman 1):
   - Isi formulir dengan data kendaraan
   - Data yang dibutuhkan: jenis, plat nomor, merek, tipe, tahun
   - Sistem akan memvalidasi input dan mencegah duplikasi plat nomor

2. **Input Uji Emisi** (Halaman 2):
   - Pilih kendaraan berdasarkan plat nomor
   - Masukkan hasil pengukuran emisi
   - Sistem akan otomatis memvalidasi dan menentukan status lulus/tidak

3. **Lihat Hasil** (Halaman 3):
   - Tampilan tabel semua hasil uji
   - Filter dan cari data
   - Export data ke CSV

## Export Data

Untuk mengekspor data ke format CSV:
1. Buka halaman "Hasil Uji"
2. Klik tombol "Export CSV"
3. File akan otomatis terdownload dengan format:
   `hasil_uji_emisi_YYYYMMDD_HHMMSS.csv`

Format CSV mencakup:
- Tanggal dan waktu uji
- Informasi kendaraan
- Hasil pengukuran emisi
- Status validasi dan kelulusan

## Troubleshooting

1. **Error "No module named 'flask'"**:
   - Pastikan virtual environment aktif
   - Jalankan ulang `pip install -r requirements.txt`

2. **Database Error**:
   - Hapus file `emisi.db` jika ada
   - Restart aplikasi untuk membuat database baru

3. **Port 5000 sudah digunakan**:
   - Hentikan proses yang menggunakan port tersebut
   - Atau ubah port di `app.py`

## Pengembangan

Untuk berkontribusi:
1. Fork repository
2. Buat branch baru
3. Commit perubahan
4. Buat pull request

## Keamanan

- Validasi input di client dan server side
- Pencegahan SQL injection dengan SQLAlchemy
- Sanitasi data sebelum display
- Error handling untuk semua operasi database

## Lisensi

[MIT License](LICENSE)

## Kontak

Untuk pertanyaan dan dukungan, silakan hubungi:
[Your Contact Information]
