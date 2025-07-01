# SINTA Scraping

Aplikasi scraping data SINTA (buku, HAKI, publikasi, penelitian, PPM, profil) untuk dosen, dengan setup otomatis.

## 🚦 Cara Pakai Singkat

1. **Clone repo & masuk folder**
   ```bash
   git clone https://github.com/2black0/sinta-scraping
   cd sinta-scraping
   ```
   
2. **Isi file .env**
   - Edit file `.env.example` menjadi `.env` di folder utama:
     ```env
     SINTA_USERNAME=isi_email_sinta_anda
     SINTA_PASSWORD=isi_password_sinta_anda
     ```

3. **Edit daftar dosen**
   - Edit file `config/dosen.yaml` untuk menambah/mengganti dosen dengan data nama dan sinta id (misal: https://sinta.kemdikbud.go.id/authors/profile/6726725) yang ingin di-scrape:
     ```yaml
     lecturers:
       - name: "Ardy Seto Priambodo"
         id: 6726725
       - name: "Nama Dosen 2"
         id: 7654321
     ```

4. **Jalankan setup otomatis (macOS/Linux, sudah teruji)**
   ```bash
   ./run.sh
   ```
   > Script Windows (`run.bat`) tersedia, namun belum diuji, oleh karena itu pengguna windows disarankan langsung ke langkah no 5.

5. **Jalankan scraping**
   - Secara default, `./run.sh` sudah otomatis menjalankan `main.py` dan menyimpan hasil scraping.
   - Jika ingin menjalankan manual (misal setelah edit dosen atau .env):
     ```bash
     python main.py                     # Semua kategori
     # atau pilih kategori tertentu:
     python main.py --buku              # Hanya data buku
     python main.py --haki              # Hanya data HAKI
     python main.py --publikasi         # Semua publikasi (Scopus, GS, WoS)
     python main.py --publikasi-scopus  # Hanya publikasi Scopus
     python main.py --publikasi-gs      # Hanya publikasi Google Scholar
     python main.py --publikasi-wos     # Hanya publikasi Web of Science
     python main.py --penelitian        # Hanya data penelitian
     python main.py --ppm               # Hanya data pengabdian masyarakat
     python main.py --profil            # Hanya data profil dosen
     # Opsi tambahan:
     python main.py --force-login       # Paksa login ulang (abaikan session lama)
     python main.py --config <file.yaml> # Gunakan file dosen custom
     # Kombinasi beberapa kategori juga bisa:
     python main.py --buku --publikasi --profil
     ```

## 📁 Output
- Hasil scraping otomatis tersimpan di folder `output-<tanggal>/` dalam format CSV.

## ℹ️ Catatan
- **Wajib**: Gunakan conda environment (bukan Python system/brew).
- **Script tested:** macOS/Linux (`run.sh`).
- **Windows:** Script `run.bat` tersedia, tapi belum diuji penuh, disarankan langsung menjalankan `python main.py`.
- **Kredensial SINTA** hanya disimpan di `.env` (tidak dibagikan).
- **Daftar dosen** hanya dari `config/dosen.yaml`.

## ❓ Bantuan
- Jika error, cek isi `.env` dan `config/dosen.yaml`.
- Pastikan sudah menjalankan `./run.sh` sebelum scraping.
- Untuk login ulang paksa: `python main.py --force-login`

---

**Happy Scraping! 🚀**
