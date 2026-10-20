# Paket publik SDN 1 Sukamanah

Status: workflow deployment sudah disiapkan lokal, belum diaktifkan atau
dipublikasikan. PR #1 tetap Draft. Tidak ada deployment pada tahap persiapan.

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

Workflow pratinjau pada commit `5f9ef2c` sudah berhasil melalui PR #1;
workflow deployment baru belum dijalankan di GitHub. Artefak pada repository publik
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
5. Setelah persetujuan, aktifkan workflow `deploy-public-site.yml` yang sudah
   disiapkan. Jangan menggabungkan PR sebelum siap: push/merge ke main akan
   memicu workflow deployment. Workflow pratinjau tetap tidak menerbitkan situs.
6. Verifikasi domain resmi, tautan, gambar, layanan publik, pemberitahuan nilai,
   dan bahwa kedua URL JSON akademik tidak dilayani oleh Pages.

Mengeluarkan dataset dari Pages tidak menghapusnya dari repository publik
atau riwayat Git. Penanganan itu terpisah dan belum dilakukan.

## Pengalihan Pages melalui akun pengelola

Lakukan hanya setelah workflow dan jadwal publikasi mendapat persetujuan baru:

1. Buka repository > Settings > Pages > Build and deployment.
2. Ganti Source dari `Deploy from a branch` menjadi `GitHub Actions`.
   Jangan mengganti domain, menghapus DNS, atau memakai tombol wizard untuk
   membuat workflow yang menerbitkan root repository.
3. Pastikan Custom domain tetap `sdn1sukamanah.my.id`, DNS check berhasil,
   dan Enforce HTTPS tetap aktif. Bila tidak sesuai, hentikan proses.
4. Pada Settings > Environments > github-pages, batasi deployment ke `main`
   dan aktifkan required reviewer bila tersedia. Jangan mengizinkan semua branch.
5. Baru setelah persetujuan akhir: ubah PR menjadi Ready, merge ke main,
   pantau build -> deploy -> verify. Jangan menjalankan `update.bat` untuk ini.

Workflow deployment hanya menerima push ke main atau workflow_dispatch pada
main dengan konfirmasi `TERBITKAN`. Kedua job build/deploy memeriksa ref dan
event. Build hanya memiliki contents:read; deploy hanya pages:write dan
id-token:write. Pemeriksaan Pages sebelum deploy adalah GET baca-saja dan
menolak sumber legacy, domain berbeda, atau HTTPS yang belum aktif.
Tidak ada langkah yang mengubah Settings/Pages/DNS.

## Pemeriksaan setelah deployment

Job verify otomatis memeriksa domain HTTPS tanpa mengikuti redirect, checksum
beranda yang sama dengan hasil build, pemberitahuan nilai, dan status halaman/
aset publik penting. Kedua URL JSON akademik hanya diperiksa dengan HEAD;
isi responsnya tidak dibaca. Harus 404 atau 410; 200/redirect dianggap gagal.
Jika pemeriksaan gagal, deployment yang sudah sukses tidak otomatis dibatalkan.

Pemeriksaan manual tambahan: buka 320/390/768/1366 px, menu sentuh/keyboard,
foto/galeri, berita, peta, dan tautan PPDB/WhatsApp tanpa mengirim pendaftaran
atau pesan. Jangan membuka stream CCTV atau mengaktifkannya. Verifikasi
download dokumen dan halaman pemberitahuan nilai. Status HEAD saja tidak
membuktikan seluruh interaksi JavaScript atau layanan eksternal berfungsi.

## Pemulihan bila gagal (memerlukan persetujuan operator)

- Build atau preflight gagal: tidak ada langkah deploy yang dijalankan.
  Tinjau nama tahap gagal; perbaiki lewat PR tanpa melonggarkan daftar izin.
- Deploy gagal: jangan menganggap situs otomatis kembali ke versi sebelumnya.
  Periksa Pages/deployment aktif dan domain terlebih dahulu; jangan hapus DNS.
- Deploy sukses tetapi verify gagal: periksa cache/checksum/domain. Hentikan
  publikasi lanjutan dan evaluasi paparan tanpa GET berkas akademik.
- Jika perlu rollback, buat commit pemulihan melalui PR ke main, hanya untuk
  perubahan publik yang bermasalah. Pertahankan builder, daftar izin, dan
  halaman pemberitahuan, lalu bangun dan validasi ulang sebelum deployment.
- Jangan force push, reset main, memilih ulang legacy main/root, atau menerbitkan
  artefak lama yang belum lolos penyaringan. Versi legacy berisi jalur akademik.
  Pratinjau lama bukan artefak Pages siap-deploy; harus dibangun ulang melalui
  builder yang telah disetujui. Artefak kedaluwarsa juga harus dibangun ulang.
- Jika belum ada rilis tersaring yang diketahui baik, gunakan halaman pemeliharaan
  publik yang disetujui, tanpa dataset, bukan seluruh repository.

Tidak ada rollback otomatis, penghapusan data, atau perubahan riwayat Git.
