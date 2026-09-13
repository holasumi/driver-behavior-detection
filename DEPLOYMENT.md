# Deployment

Website publik (Sites): https://driver-monitor-sumii.sakinahfarah17.chatgpt.site

Pembaruan versi 2 berhasil diterbitkan pada 13 September 2026, dengan akses publik tanpa login.

Repositori publik: https://github.com/holasumi/driver-behavior-detection

Alamat GitHub Pages yang dikonfigurasi: https://holasumi.github.io/driver-behavior-detection/

Status Pages pada 13 September 2026: sumber `gh-pages` sudah benar, tetapi API build GitHub mengembalikan HTTP 500 dan belum menghasilkan deployment. Gunakan tautan Sites di atas yang sudah berhasil dan merespons HTTP 200 tanpa login.

GitHub Pages menggunakan cabang `gh-pages` berisi `web/dist`. Perbarui setelah commit dengan:

```sh
git push origin main
git subtree push --prefix web/dist origin gh-pages
```

Kamera diproses di browser masing-masing pengunjung, tanpa backend Python, upload video, atau API key. Pilih Mulai kamera lalu kalibrasi 4 detik; pilih Coba simulasi untuk mencoba tanpa kamera.
