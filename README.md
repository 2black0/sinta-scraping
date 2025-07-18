# SINTA Scraping CLI

Aplikasi scraping data SINTA (buku, HAKI, publikasi, penelitian, PPM, profil) untuk dosen. Versi CLI yang menggunakan login berbasis request dengan session management otomatis.

## 🚀 Cara Pakai

### 1. **Setup Environment**
```bash
# Install dependencies
pip install requests>=2.32.3 beautifulsoup4>=4.12.3 python-dotenv>=1.0.0
```

### 2. **Konfigurasi Login**
Buat file `.env` di folder utama:
```env
SINTA_USERNAME=email_sinta_anda
SINTA_PASSWORD=password_sinta_anda
```

### 3. **Daftar Dosen**
Edit file `dosen.txt` - satu ID SINTA per baris:
```
6726725
7654321
8765432
# Komentar diawali dengan #
```
> ID SINTA dari URL profil: `https://sinta.kemdikbud.go.id/authors/profile/6726725`

### 4. **Jalankan Scraping**
```bash
# Scrape semua kategori
python main-cli.py

# Scrape kategori tertentu
python main-cli.py --buku              # Data buku
python main-cli.py --haki              # Data HAKI
python main-cli.py --publikasi         # Semua publikasi
python main-cli.py --publikasi-scopus  # Publikasi Scopus
python main-cli.py --publikasi-gs      # Publikasi Google Scholar
python main-cli.py --publikasi-wos     # Publikasi Web of Science
python main-cli.py --penelitian        # Data penelitian
python main-cli.py --ppm               # Pengabdian masyarakat
python main-cli.py --profil            # Profil dosen

# Opsi tambahan
python main-cli.py --force-login       # Paksa login ulang
python main-cli.py --config custom.txt # File dosen custom
```

## 📁 Output

Hasil scraping tersimpan di folder `output-DDMMYYYY/` dalam format CSV:
- `buku.csv` - Data buku
- `haki.csv` - Data HAKI  
- `publikasi_scopus.csv` - Publikasi Scopus
- `publikasi_gs.csv` - Publikasi Google Scholar
- `publikasi_wos.csv` - Publikasi Web of Science
- `penelitian.csv` - Data penelitian
- `ppm.csv` - Pengabdian masyarakat
- `profil.csv` - Profil dosen lengkap dengan nama, universitas, prodi, dan SINTA Score

## ✨ Fitur

- **Login otomatis** menggunakan request
- **Session management** - tidak perlu login berulang, session tersimpan di `.config/`
- **Scraping selektif** - pilih kategori yang diinginkan
- **Data lengkap** - profil mencakup nama asli, universitas, program studi, dan SINTA Score
- **Output terstruktur** - CSV dengan header yang jelas
- **Error handling** - pesan error yang informatif
- **Konfigurasi fleksibel** - support file TXT dengan komentar

## 🔧 Troubleshooting

- **Login gagal**: Periksa kredensial di `.env`
- **Session expired**: Gunakan `--force-login`
- **ID tidak ditemukan**: Periksa format di `dosen.txt`
- **Error dependency**: Install ulang packages: `pip install requests>=2.32.3 beautifulsoup4>=4.12.3 python-dotenv>=1.0.0`
- **Folder .config tidak ada**: Akan dibuat otomatis saat login pertama

## 📝 Format Data

### Profil Dosen
Data profil lengkap dengan kolom:
- ID Sinta, Nama, Universitas, Program Studi
- SINTA Score Overall, SINTA Score 3Yr
- Jumlah publikasi (Scopus, Google Scholar, WoS)
- H-Index dan i10-Index
- Dan informasi lainnya

### Publikasi
Data publikasi dengan informasi:
- Judul artikel, nama jurnal
- Quartile (untuk Scopus/WoS)
- Penulis, tahun, sitasi
- DOI dan link artikel

---

**Happy Scraping! 🎉**