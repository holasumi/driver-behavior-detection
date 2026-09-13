# Deployment

Website publik (Sites): https://driver-monitor-sumii.sakinahfarah17.chatgpt.site

Pembaruan versi 3 berhasil diterbitkan pada 13 September 2026, dengan akses publik tanpa login.

Repositori publik: https://github.com/holasumi/driver-behavior-detection

Alamat GitHub Pages yang dikonfigurasi: https://holasumi.github.io/driver-behavior-detection/

Status Pages pada 13 September 2026: konfigurasi sumber telah disegarkan dan build berstatus `building`, tetapi URL masih merespons 404. GitHub mengonfirmasi gangguan layanan Pages: https://www.githubstatus.com/incidents/0rn90wk115q9. Tautan Sites versi 3 tetap tersedia; kedua tulisan pembuka sudah dihapus. URL GitHub Pages belum dapat dinyatakan aktif sampai build selesai.

GitHub Pages menggunakan cabang `gh-pages` berisi `web/dist`. Perbarui setelah commit dengan:

```sh
git push origin main
git subtree push --prefix web/dist origin gh-pages
```

Kamera diproses di browser masing-masing pengunjung, tanpa backend Python, upload video, atau API key. Pilih Mulai kamera lalu kalibrasi 4 detik; pilih Coba simulasi untuk mencoba tanpa kamera.
