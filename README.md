# SINTA Scraping CLI

Aplikasi command-line untuk scraping data SINTA (Science and Technology Index) yang mencakup data profil dosen, publikasi, penelitian, buku, HAKI, dan pengabdian masyarakat.

## ✨ Fitur

- **🎯 Scraping Multi-Kategori**: Profil, publikasi (Scopus/Google Scholar/WoS), penelitian, buku, HAKI, PPM
- **⚡ Session Management**: Login otomatis dengan cookie persistence
- **📊 Multiple Output**: CSV files terstruktur untuk setiap kategori
- **🔧 CLI Flexible**: Argumen untuk scraping kategori spesifik atau semua data
- **🛡️ Error Handling**: Robust error handling dan retry mechanism

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install requests beautifulsoup4 python-dotenv
```

### 2. Setup kredensial SINTA (wajib)
rename `.env.example`menjadi `.env`dan isi
```bash
SINTA_USERNAME=emailsinta@example.com
SINTA_PASSWORD=passwordsinta
```

### 3. Setup daftar dosen
```bash
# Edit file dosen.txt dan masukkan ID SINTA (satu per baris):
6726725
6741317
6007349
```
> **💡 Tip**: ID SINTA dari URL profil: `https://sinta.kemdikbud.go.id/authors/profile/6726725`


### 4. Jalankan scraping
```bash
python sinta-cli.py                          # Semua kategori
python sinta-cli.py --profil                 # Profil dosen saja
python sinta-cli.py --publikasi-scopus       # Publikasi Scopus saja
python sinta-cli.py --help                   # Lihat semua opsi
```

---

## 📁 Output

Hasil scraping tersimpan di folder `output-DDMMYYYY/` dalam format CSV:

```
output-19072025/
├── profil.csv               # Profil dosen (nama, institusi, bidang, dll)
├── buku.csv                 # Data buku yang diterbitkan
├── haki.csv                 # Data HAKI/paten
├── penelitian.csv           # Data penelitian
├── ppm.csv                  # Pengabdian masyarakat
├── publikasi_scopus.csv     # Publikasi Scopus
├── publikasi_gs.csv         # Publikasi Google Scholar
└── publikasi_wos.csv        # Publikasi Web of Science
```

---

## � Lisensi

Proyek ini menggunakan MIT License - lihat file [LICENSE](LICENSE) untuk detail.

---

**Disclaimer**: Aplikasi ini untuk tujuan penelitian dan edukasi. Patuhi terms of service SINTA.

---

**Happy Scraping! 🎉**
