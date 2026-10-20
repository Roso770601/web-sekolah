# Paket publik SDN 1 Sukamanah

Status: persiapan lokal / artefak pratinjau saja. Tidak ada deployment.

## Build lokal

Gunakan Python 3.10+ dan direktori keluaran baru di luar repository:

```powershell
python scripts/build_public_site.py --output C:\lokasi-uji\public-site --report C:\lokasi-uji\inventory.json
python scripts/test_public_build.py
python scripts/build_public_site.py --check-only --output C:\lokasi-uji\public-site
```

Direktori keluaran yang sudah ada ditolak, bukan dihapus atau ditimpa.
Laporan berisi nama berkas dan SHA-256, disimpan di luar paket website.
Folder hasil adalah pratinjau, bukan backup. Jangan melayani root repository
ketika memeriksa hasil; layani hanya direktori `public-site`.

## Apa yang diterbitkan dalam pratinjau

- `public-files.txt` menyebut 160 berkas sumber satu per satu, tanpa wildcard.
- Sembilan salinan kompatibilitas/gaya dibuat di hasil build: delapan alias
  gambar lama dan `style.css`. Tidak ada sumber halaman yang ditulis ulang.
- `nilai/nilai.html` dibuat dari pemberitahuan tetap, bukan disalin dari portal.
- Total: 170 berkas. Domain CNAME harus persis `sdn1sukamanah.my.id`.
- Satu-satunya JSON yang diizinkan adalah `berita/data.json`.
- Tidak ada Excel, Python, BAT, dataset akademik, file tersembunyi, atau symlink.
- Build memeriksa daftar berkas lengkap, kesamaan isi dengan sumber publik,
  tautan lokal HTML/CSS, gambar metadata pada domain sendiri, dan tautan berita
  yang dibentuk JavaScript. Tidak menghubungi layanan eksternal.

Halaman login tetap memiliki alamat dan logika lama. Setelah diarahkan ke
`nilai/nilai.html`, pengguna melihat "Layanan Nilai Belum Tersedia".
Halaman sumber portal dan seluruh JSON akademik tidak dibaca oleh builder.
Ini belum menggantikan autentikasi aman saat layanan nilai dibuka kelak.

## Workflow

`build-public-site.yml` hanya berjalan secara manual atau pada pull request
ke `main`. Tidak ada pemicu `push`, `pull_request_target`, langkah deploy,
izin `pages: write`, maupun `id-token: write`. Action dikunci ke hash commit
resmi; checkout tidak menyimpan kredensial. Hasil unggahan:

- `public-site-preview`: website saja, kedaluwarsa tujuh hari.
- `public-site-inventory`: daftar berkas dan checksum, terpisah dari website.

Workflow ini belum dijalankan di GitHub. Artefak pada repository publik
harus dianggap dapat diakses pihak lain, sehingga pemeriksaan dijalankan
sebelum upload. Pemeriksaan tidak membuktikan asal-usul setiap konten publik.

## Sebelum publikasi resmi (memerlukan persetujuan baru)

1. Tinjau/commit/push hanya berkas persiapan yang disetujui melalui Git terpisah.
   `update.bat` tidak digunakan: pengamannya akan menolak perubahan selain
   `index.html` serta berkas akademik yang masih terlacak.
2. Periksa Settings > Pages. Jangan merge ke main saat publikasi lama dari
   branch masih aktif: itu dapat menerbitkan ulang seluruh sumber lama.
3. Pengelola berwenang mengalihkan sumber Pages ke GitHub Actions sebelum
   pembaruan main yang akan memicu publikasi lama, pada waktu yang disetujui.
   Pengaturan domain dan HTTPS diverifikasi tanpa mengubah DNS sembarangan.
4. Jalankan build pratinjau, tinjau inventaris/artefak dan halaman pemberitahuan.
5. Tambahkan/alihkan workflow deployment tersendiri setelah persetujuan, dengan
   validasi yang sama dan hanya artefak publik tersebut. Workflow sekarang
   sengaja tidak menyediakan deployment.
6. Verifikasi domain resmi, tautan, gambar, layanan publik, pemberitahuan nilai,
   dan bahwa kedua URL JSON akademik tidak dilayani oleh Pages.

Mengeluarkan dataset dari Pages tidak menghapusnya dari repository publik
atau riwayat Git. Penanganan itu terpisah dan belum dilakukan.
