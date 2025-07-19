# SINTA Scraping

Aplikasi untuk scraping data SINTA (Science and Technology Index) mencakup data buku, HAKI, publikasi, penelitian, PPM, dan profil dosen. Project ini memiliki 2 fitur utama:

## 🌟 Fitur Utama

### 1. 🌐 **Web Interface** 
Interface web modern dan user-friendly untuk operasional sehari-hari:
- Tampilan sederhana dengan kontrol panel untuk konfigurasi
- CSV viewer untuk melihat hasil scraping
- Grid layout untuk seleksi kategori data
- Dropdown download untuk file hasil
- Real-time progress monitoring

### 2. ⌨️ **CLI (Command Line Interface)**
Interface command line yang powerful untuk automasi dan scripting:
- Scraping batch dengan argumen fleksibel
- Session management otomatis
- Support konfigurasi file custom
- Error handling yang robust

---

## 🚀 Quick Start

### **Web Interface (Recommended)**
```bash
# Install dependencies
pip install flask requests beautifulsoup4 python-dotenv charset-normalizer

# Run web interface
python sinta-web.py
```
**🔗 Akses: http://localhost:5000**

### **CLI Version**
```bash
# Install dependencies
pip install requests beautifulsoup4 python-dotenv charset-normalizer

# Run CLI directly
python sinta-cli.py --help
```

---

## ⚙️ Setup & Konfigurasi

### 1. **Kredensial Login**
Buat file `.env` di folder utama:
```env
SINTA_USERNAME=email_sinta_anda
SINTA_PASSWORD=password_sinta_anda
```

### 2. **Daftar Dosen**
Edit file `dosen.txt` - satu ID SINTA per baris:
```
6726725
7654321
8765432
# Komentar diawali dengan #
```
> ID SINTA dari URL profil: `https://sinta.kemdikbud.go.id/authors/profile/6726725`

---

## 📖 Penggunaan

### **🌐 Web Interface**
1. Jalankan web interface: `python sinta-web.py`
2. Buka browser ke http://localhost:5000
3. Atur ID dosen via interface web
4. Pilih kategori data yang diinginkan
5. Klik tombol scraping dan monitor progress
6. Download hasil via dropdown download
7. Gunakan CSV viewer untuk melihat data

### **⌨️ CLI Interface**
```bash
# Scrape semua kategori
python sinta-cli.py

# Scrape kategori tertentu
python sinta-cli.py --profil            # Profil dosen
python sinta-cli.py --buku              # Data buku
python sinta-cli.py --haki              # Data HAKI
python sinta-cli.py --penelitian        # Data penelitian
python sinta-cli.py --ppm               # Pengabdian masyarakat
python sinta-cli.py --publikasi-scopus  # Publikasi Scopus
python sinta-cli.py --publikasi-gs      # Publikasi Google Scholar
python sinta-cli.py --publikasi-wos     # Publikasi Web of Science

# Opsi tambahan
python sinta-cli.py --force-login       # Paksa login ulang
python sinta-cli.py --config custom.txt # File dosen custom
```

---

## 📁 Output & Struktur File

Hasil scraping tersimpan di folder `output-DDMMYYYY/` dalam format CSV:

```
output-19072025/
├── profil.csv               # Profil dosen lengkap (18 kolom)
├── buku.csv                 # Data buku (9 kolom)
├── haki.csv                 # Data HAKI (7 kolom)
├── penelitian.csv           # Data penelitian (10 kolom)
├── ppm.csv                  # Pengabdian masyarakat (10 kolom)
├── publikasi_scopus.csv     # Publikasi Scopus (9 kolom)
├── publikasi_gs.csv         # Publikasi Google Scholar (8 kolom)
└── publikasi_wos.csv        # Publikasi Web of Science (15 kolom)
```

### **Struktur Project**
```
sinta-scraping/
├── sinta-cli.py             # CLI application
├── sinta-web.py             # Web interface launcher
├── dosen.txt                # Daftar ID dosen SINTA
├── .env                     # Kredensial login SINTA
├── README.md                # Dokumentasi
├── output-DDMMYYYY/         # Folder hasil scraping
└── web/                     # Web interface files
    ├── app.py               # Flask application
    ├── run.py               # Web launcher
    ├── requirements.txt     # Dependencies
    ├── static/              # CSS & JavaScript
    └── templates/           # HTML templates
```

---

## 🔧 Troubleshooting

### **Common Issues**
- **Login gagal**: Periksa kredensial di file `.env`
- **Session expired**: Gunakan `--force-login` pada CLI
- **ID tidak ditemukan**: Periksa format ID di `dosen.txt`
- **Flask import error**: Install dependencies: `pip install flask`
- **Port 5000 sudah digunakan**: Ubah port di `web/app.py`

### **Data Format**
- Semua file CSV menggunakan encoding UTF-8
- Anggota penelitian/PPM dipisah dengan tanda titik koma (;)
- Data yang tidak tersedia ditandai dengan "N/A"
- ID Sinta dan Nama Sinta ada di setiap file untuk referensi

---

**Happy Scraping! 🎉**

**Quick Commands:**
- **🌐 Web**: `python sinta-web.py` → http://localhost:5000
- **⌨️ CLI**: `python sinta-cli.py --help`