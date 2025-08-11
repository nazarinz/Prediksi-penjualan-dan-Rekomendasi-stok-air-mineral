import streamlit as st

st.title("Tentang Sistem & Dokumentasi Teknis")

st.markdown("""
### Deskripsi Sistem
Sistem ini dibangun sebagai alat bantu dalam melakukan **prediksi penjualan dan perencanaan stok air mineral** berbasis website untuk CV. Gari Pratama Indosuka, menggunakan pendekatan **Machine Learning Random Forest Regression**.

Sistem terdiri dari beberapa modul utama:
- Memuat data penjualan bulanan dari file `data.csv` (default)
- **Upload data manual** di halaman Dashboard untuk memperbarui dataset
- Prediksi penjualan menggunakan model Random Forest
- Rekomendasi stok dengan safety stock
- Visualisasi historis penjualan untuk analisis tren

---
### Fitur Upload Data Manual
Sistem mendukung **upload data manual** di halaman Dashboard untuk memperbarui dataset yang digunakan dalam analisis:

#### Lokasi Fitur Upload:
- **Hanya tersedia di halaman Dashboard**
- Data yang diupload akan digunakan di semua halaman
- Session state memastikan konsistensi data

#### Format Data yang Diperlukan:
- **File format**: CSV
- **Encoding**: UTF-8
- **Kolom wajib**: `Tahun`, `Bulan`, `Nama Item`, `total_jumlah`

#### Validasi Data:
- Tahun: 1900-2100
- Bulan: 1-12
- Nama Item: teks
- total_jumlah: angka positif

#### Cara Menggunakan:
1. Siapkan file CSV dengan format yang sesuai
2. Upload file di halaman Dashboard menggunakan widget upload
3. Sistem akan memvalidasi dan memproses data
4. Data akan tersimpan dalam session state
5. Semua halaman akan menggunakan data yang diupload
6. Jika tidak upload, sistem menggunakan data.csv default

---
### Model Prediksi
- **Algoritma**: Random Forest Regression
- **Library**: scikit-learn
- **File model**: `best_model.joblib` (dilatih sebelumnya)
- **Target**: `total_jumlah` (jumlah penjualan per bulan)

#### Fitur-Fitur Input:
| Fitur             | Deskripsi                                      |
|------------------|-----------------------------------------------|
| Tahun, Bulan     | Informasi waktu                                |
| quarter          | Kuartal (1–4)                                  |
| is_start_year    | Awal tahun? (1: ya, 0: tidak)                  |
| is_end_year      | Akhir tahun? (1: ya, 0: tidak)                 |
| lag_1, lag_2, lag_3 | Penjualan pada 1–3 bulan sebelumnya         |
| ma_3, ma_6       | Moving average 3 dan 6 bulan terakhir          |
| diff_1           | Selisih penjualan dari bulan sebelumnya        |

---
### Cara Kerja Sistem
1. **Data penjualan** diambil dari file `data.csv` (default) atau file yang diupload
2. Sistem melakukan **validasi kolom** dan pemrosesan fitur
3. Model melakukan **prediksi penjualan** berdasarkan fitur yang ada
4. Sistem menghitung **rekomendasi stok** dengan safety stock
5. Hasil dapat diunduh dan divisualisasikan dalam bentuk grafik & tabel

---
### Tujuan Sistem
- Membantu manajemen stok lebih efisien
- Mencegah kelebihan atau kekurangan barang
- Menyediakan insight berbasis data historis
- **Memungkinkan update data secara real-time** melalui fitur upload di Dashboard

---
### Pengembang
- **Nama**: Nazarudin Zaini
- **Universitas**: Universitas Nusa Putra
- **Judul Skripsi**: IMPLEMENTASI RANDOM FOREST REGRESSION UNTUK PREDIKSI PENJUALAN DAN REKOMENDASI STOK AIR MINERAL BERBASIS WEBSITE DI CV. GARI PRATAMA INDOSUKA

_Skripsi ini dikembangkan sebagai bagian dari pemenuhan tugas akhir program Sarjana Teknik Informatika._
""")

st.info("Jika ada pembaruan model, pastikan untuk mengganti file `best_model.joblib` di direktori project.")

# Additional information about data upload
st.subheader("📤 Panduan Upload Data")

st.markdown("""
### Lokasi Fitur Upload:
**Fitur upload data manual hanya tersedia di halaman Dashboard**

### Langkah-langkah Upload Data:

1. **Siapkan File CSV**
   - Gunakan format yang sesuai dengan contoh
   - Pastikan encoding UTF-8
   - Validasi data sebelum upload

2. **Upload File di Dashboard**
   - Buka halaman Dashboard
   - Klik tombol "Browse files" di widget upload
   - Pilih file CSV yang sudah disiapkan
   - Tunggu proses validasi dan pemrosesan

3. **Validasi Otomatis**
   - Sistem akan memeriksa format data
   - Menampilkan warning jika ada masalah
   - Memproses data jika valid

4. **Hasil Upload**
   - Dashboard akan diperbarui otomatis
   - Data tersimpan dalam session state
   - Dapat digunakan di semua halaman

### Konsistensi Data:
- Data yang diupload akan digunakan di semua halaman
- Session state memastikan data konsisten
- Tidak perlu upload ulang di setiap halaman

### Troubleshooting:

**Error: "Kolom yang diperlukan tidak ditemukan"**
- Pastikan kolom: `Tahun`, `Bulan`, `Nama Item`, `total_jumlah`
- Periksa nama kolom (case sensitive)

**Error: "Data tidak valid"**
- Periksa range tahun (1900-2100)
- Periksa range bulan (1-12)
- Pastikan total_jumlah positif

**Error: "File tidak dapat dibaca"**
- Pastikan format CSV
- Periksa encoding file
- Coba buka file di text editor
""")


