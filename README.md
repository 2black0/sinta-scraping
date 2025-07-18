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

## 📊 Analisis Data

### Menggunakan Pandas
```python
import pandas as pd

# Baca data profil
profil = pd.read_csv('output-18072025/profil.csv')

# Statistik dasar
print(profil[['SINTA Score Overall', 'Scopus Article', 'GScholar Citation']].describe())

# Filter dosen dengan skor SINTA > 80
high_score = profil[profil['SINTA Score Overall'].astype(float) > 80]

# Gabungkan data publikasi dengan profil
scopus = pd.read_csv('output-18072025/publikasi_scopus.csv')
publikasi_per_dosen = scopus.groupby('ID Sinta').size().reset_index(name='Jumlah Publikasi')
merged = profil.merge(publikasi_per_dosen, on='ID Sinta', how='left')
```

### Visualisasi Data
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Distribusi SINTA Score
plt.figure(figsize=(10, 6))
plt.hist(profil['SINTA Score Overall'].astype(float), bins=20, alpha=0.7)
plt.title('Distribusi SINTA Score Overall')
plt.xlabel('SINTA Score')
plt.ylabel('Frekuensi')
plt.show()

# Korelasi antara Scopus dan Google Scholar
plt.figure(figsize=(8, 6))
plt.scatter(profil['Scopus Article'].astype(int), profil['GScholar Article'].astype(int))
plt.xlabel('Scopus Articles')
plt.ylabel('Google Scholar Articles')
plt.title('Korelasi Publikasi Scopus vs Google Scholar')
plt.show()
```

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

## 📋 Contoh Data

### Contoh profil.csv
```csv
Nama Sinta,ID Sinta,Universitas,Program Studi,SINTA Score Overall,SINTA Score 3Yr,Scopus Article,Scopus Citation,Scopus Cited Document,Scopus H-Index,Scopus i10-Index,Scopus G-Index,GScholar Article,GScholar Citation,GScholar Cited Document,GScholar H-Index,GScholar i10-Index,GScholar G-Index
Dr. John Doe,6726725,Institut Teknologi Bandung,Teknik Informatika,85.5,78.2,25,350,23,12,15,18,45,520,42,15,22,28
```

### Contoh publikasi_scopus.csv
```csv
Judul Artikel,Nama Jurnal,Quartile,Penulis,Tahun,Sitasi,Link,ID Sinta,Nama Sinta
"Machine Learning for Data Analysis",IEEE Transactions on Pattern Analysis,Q1,"John Doe; Jane Smith",2023,15,https://doi.org/10.1109/example,6726725,Dr. John Doe
```

### Contoh penelitian.csv
```csv
Judul Penelitian,Ketua Penelitian,Sumber Dana,Anggota Penelitian,Tahun,Besar Dana,Status,Sumber,ID Sinta,Nama Sinta
"Pengembangan Sistem AI untuk Pendidikan",Dr. John Doe,Kementerian Pendidikan,"Dr. John Doe; Dr. Jane Smith; Dr. Bob Wilson",2023,500000000,Selesai,SIMLITABMAS,6726725,Dr. John Doe
```

## 📚 Interpretasi Data

### Metrik Profil Dosen
- **SINTA Score Overall**: Skor kumulatif berdasarkan semua publikasi
- **SINTA Score 3Yr**: Skor berdasarkan publikasi 3 tahun terakhir
- **H-Index**: Jumlah artikel yang dikutip minimal h kali
- **i10-Index**: Jumlah artikel yang dikutip minimal 10 kali
- **G-Index**: Varian H-Index yang memberikan bobot lebih pada sitasi tinggi

### Quartile Jurnal
- **Q1**: 25% jurnal teratas dalam bidang (impact factor tertinggi)
- **Q2**: 25%-50% jurnal dalam bidang
- **Q3**: 50%-75% jurnal dalam bidang
- **Q4**: 25% jurnal terbawah dalam bidang

### Status Penelitian/PPM
- **Selesai**: Penelitian telah diselesaikan
- **Sedang Berjalan**: Penelitian masih dalam tahap pelaksanaan
- **Usulan**: Proposal yang diajukan
- **Ditolak**: Proposal yang tidak lolos evaluasi

## 🎯 Best Practices

### Penggunaan Aplikasi
1. **Gunakan file dosen.txt yang terstruktur** dengan ID yang valid
2. **Jalankan scraping di luar jam sibuk** untuk menghindari rate limiting
3. **Backup data secara berkala** karena struktur SINTA dapat berubah
4. **Verifikasi data hasil scraping** dengan sampling manual

### Analisis Data
1. **Bersihkan data** sebelum analisis statistik
2. **Perhatikan missing values** yang ditandai "N/A"
3. **Normalisasi data numerik** untuk perbandingan yang akurat
4. **Gunakan visualisasi** untuk memahami pola data

### Etika Scraping
1. **Patuhi robots.txt** dan terms of service SINTA
2. **Jangan melakukan scraping berlebihan** yang dapat mengganggu layanan
3. **Gunakan data untuk keperluan akademis** dan penelitian
4. **Hormati privasi dan hak cipta** data yang di-scrape

---

**Happy Scraping! 🎉**