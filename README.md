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

```
output-18072025/
├── buku.csv                 # Data buku (9 kolom)
├── haki.csv                 # Data HAKI (7 kolom)
├── publikasi_scopus.csv     # Publikasi Scopus (9 kolom)
├── publikasi_gs.csv         # Publikasi Google Scholar (8 kolom)
├── publikasi_wos.csv        # Publikasi Web of Science (15 kolom)
├── penelitian.csv           # Data penelitian (10 kolom)
├── ppm.csv                  # Pengabdian masyarakat (10 kolom)
└── profil.csv               # Profil dosen lengkap (18 kolom)
```

**Catatan Format**:
- Semua file CSV menggunakan encoding UTF-8
- Anggota penelitian/PPM dipisah dengan tanda titik koma (;)
- Data yang tidak tersedia ditandai dengan "N/A"
- Kolom ID Sinta dan Nama Sinta ada di setiap file untuk referensi
- Judul dengan tanda kutip akan di-escape dengan benar dalam CSV
- Data numerik (sitasi, dana, skor) disimpan sebagai string untuk konsistensi

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

## � Format Data Output

### 1. 📖 Data Buku (`buku.csv`)
| Header | Deskripsi |
|--------|-----------|
| `Judul Buku` | Judul lengkap buku |
| `Kategori Buku` | Kategori/jenis buku |
| `Penulis` | Nama-nama penulis |
| `Penerbit` | Nama penerbit |
| `Tahun` | Tahun terbit |
| `Kota` | Kota terbit |
| `ISBN` | Nomor ISBN |
| `ID Sinta` | ID SINTA dosen |
| `Nama Sinta` | Nama dosen di SINTA |

### 2. 🏛️ Data HAKI (`haki.csv`)
| Header | Deskripsi |
|--------|-----------|
| `Judul HAKI` | Judul karya HAKI |
| `Penemu` | Nama penemu/inventor |
| `Jenis HAKI` | Jenis hak kekayaan intelektual |
| `Nomor HAKI` | Nomor pendaftaran HAKI |
| `Tahun` | Tahun pendaftaran |
| `ID Sinta` | ID SINTA dosen |
| `Nama Sinta` | Nama dosen di SINTA |

### 3. 📚 Data Publikasi Scopus (`publikasi_scopus.csv`)
| Header | Deskripsi |
|--------|-----------|
| `Judul Artikel` | Judul artikel publikasi |
| `Nama Jurnal` | Nama jurnal publikasi |
| `Quartile` | Kuartil jurnal (Q1, Q2, Q3, Q4) |
| `Penulis` | Daftar penulis |
| `Tahun` | Tahun publikasi |
| `Sitasi` | Jumlah sitasi |
| `Link` | Link ke artikel |
| `ID Sinta` | ID SINTA dosen |
| `Nama Sinta` | Nama dosen di SINTA |

### 4. 🎓 Data Publikasi Google Scholar (`publikasi_gs.csv`)
| Header | Deskripsi |
|--------|-----------|
| `Judul Artikel` | Judul artikel publikasi |
| `Nama Jurnal` | Nama jurnal publikasi |
| `Penulis` | Daftar penulis |
| `Tahun` | Tahun publikasi |
| `Sitasi` | Jumlah sitasi |
| `Link` | Link ke artikel |
| `ID Sinta` | ID SINTA dosen |
| `Nama Sinta` | Nama dosen di SINTA |

### 5. 🔬 Data Publikasi Web of Science (`publikasi_wos.csv`)
| Header | Deskripsi |
|--------|-----------|
| `Judul Artikel` | Judul artikel publikasi |
| `Nama Jurnal` | Nama jurnal publikasi |
| `Quartile` | Kuartil jurnal (Q1, Q2, Q3, Q4) |
| `Edition` | Edisi jurnal |
| `Link Jurnal` | Link ke halaman jurnal |
| `Penulis` | Daftar penulis |
| `Urutan Penulis` | Urutan penulis dalam artikel |
| `Total Penulis` | Total jumlah penulis |
| `Tahun` | Tahun publikasi |
| `Sitasi` | Jumlah sitasi |
| `Terindex Scopus` | Status terindeks Scopus (Yes/No) |
| `DOI` | Digital Object Identifier |
| `Link` | Link ke artikel |
| `ID Sinta` | ID SINTA dosen |
| `Nama Sinta` | Nama dosen di SINTA |

### 6. 🔬 Data Penelitian (`penelitian.csv`)
| Header | Deskripsi |
|--------|-----------|
| `Judul Penelitian` | Judul lengkap penelitian |
| `Ketua Penelitian` | Nama ketua penelitian |
| `Sumber Dana` | Sumber pendanaan penelitian |
| `Anggota Penelitian` | Daftar anggota penelitian (dipisah dengan ;) |
| `Tahun` | Tahun pelaksanaan |
| `Besar Dana` | Jumlah dana penelitian |
| `Status` | Status penelitian |
| `Sumber` | Sumber informasi |
| `ID Sinta` | ID SINTA dosen |
| `Nama Sinta` | Nama dosen di SINTA |

### 7. 🤝 Data Pengabdian Masyarakat (`ppm.csv`)
| Header | Deskripsi |
|--------|-----------|
| `Judul PPM` | Judul pengabdian masyarakat |
| `Ketua PPM` | Nama ketua pengabdian |
| `Skim PPM` | Skema pengabdian |
| `Anggota PPM` | Daftar anggota pengabdian (dipisah dengan ;) |
| `Tahun` | Tahun pelaksanaan |
| `Besar Dana` | Jumlah dana pengabdian |
| `Status` | Status pengabdian |
| `Sumber` | Sumber informasi |
| `ID Sinta` | ID SINTA dosen |
| `Nama Sinta` | Nama dosen di SINTA |

### 8. 👤 Data Profil Dosen (`profil.csv`)
| Header | Deskripsi |
|--------|-----------|
| `Nama Sinta` | Nama dosen di SINTA |
| `ID Sinta` | ID SINTA dosen |
| `Universitas` | Nama universitas |
| `Program Studi` | Program studi/jurusan |
| `SINTA Score Overall` | Skor SINTA keseluruhan |
| `SINTA Score 3Yr` | Skor SINTA 3 tahun terakhir |
| `Scopus Article` | Jumlah artikel Scopus |
| `Scopus Citation` | Jumlah sitasi Scopus |
| `Scopus Cited Document` | Jumlah dokumen tersitasi Scopus |
| `Scopus H-Index` | H-Index Scopus |
| `Scopus i10-Index` | i10-Index Scopus |
| `Scopus G-Index` | G-Index Scopus |
| `GScholar Article` | Jumlah artikel Google Scholar |
| `GScholar Citation` | Jumlah sitasi Google Scholar |
| `GScholar Cited Document` | Jumlah dokumen tersitasi Google Scholar |
| `GScholar H-Index` | H-Index Google Scholar |
| `GScholar i10-Index` | i10-Index Google Scholar |
| `GScholar G-Index` | G-Index Google Scholar |

---

**Happy Scraping! 🎉**