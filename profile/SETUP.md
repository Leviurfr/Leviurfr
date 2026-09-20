# Pemasangan (sekitar 5 menit)

1. Buat repositori **publik** di GitHub dengan nama yang persis sama dengan username kamu.
2. Unggah seluruh isi folder ini ke repositori itu: `README.md`, `assets/`, `scripts/`, dan `.github/`.
   Folder `.github` kadang terlewat saat drag-and-drop dari Explorer/Finder. Jika terlewat, pakai
   **Add file > Create new file**, ketik `.github/workflows/profil.yml`, lalu tempel isi file itu.
3. Buka `README.md`, cari-ganti semua `USERNAME` dengan username GitHub kamu.
4. Buka **Settings > Actions > General > Workflow permissions**, pilih **Read and write permissions**, simpan.
5. Buka tab **Actions**, pilih workflow **Profil**, klik **Run workflow**. Setelah 1 sampai 2 menit
   kartu statistik, ular kontribusi, dan kalender 3D akan muncul. Selanjutnya diperbarui otomatis tiap hari.

## GIF Subaru

Versi HD dari Tenor (`...AAAAd`) berukuran sekitar 36 MB. GitHub menyaring gambar eksternal lewat proxy
yang, menurut berbagai laporan, menolak file di atas kira-kira 5 MB, dan file sebesar itu juga membuat
profil lambat dibuka. Karena itu README memakai versi kecil (165x255).

Untuk versi lebih tajam: unduh GIF-nya, kompres di ezgif.com (Optimize atau Resize) sampai di bawah 5 MB,
simpan sebagai `assets/subaru.gif`, lalu di `README.md` ganti `src` gambar Subaru menjadi `assets/subaru.gif`.

## Yang perlu kamu isi sendiri

- Bagian **Tentang** di `README.md`: sesuaikan dengan keadaan sebenarnya.
- **Proyek**: nama, deskripsi, dan tag ada di bagian bawah `build_assets.py` (fungsi `build_card`).
  Ubah, jalankan `python3 build_assets.py`, lalu unggah `assets/card-*.svg` yang baru.
  Ubah juga tautan repositori di `README.md`.
- **Warna dan font**: konstanta di bagian atas `build_assets.py`. Font memakai font bawaan sistem
  pembaca (Georgia dan monospace), jadi tampilannya sedikit berbeda antar perangkat.

## Jika sesuatu tidak muncul

- Ular atau kalender 3D kosong: workflow belum dijalankan, atau izin di langkah 4 belum diubah.
- Kartu statistik masih bertuliskan "Menunggu data pertama": job **Kartu statistik** belum selesai atau gagal.
  Buka tab Actions untuk melihat lognya. Kartu hanya menghitung repositori publik.
