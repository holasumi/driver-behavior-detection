# Driver Monitor

Website HTML/CSS/JavaScript untuk memantau mata, mulut, dan arah kepala menggunakan kamera perangkat. Versi Python/OpenCV tersedia untuk desktop. Tidak memakai API Claude/GPT, tidak memerlukan API key, dan tidak mengunggah video.

## Website

Klik **Mulai kamera**, izinkan kamera, lalu lihat lurus dengan mata terbuka dan mulut tertutup selama 4 detik untuk kalibrasi. Pilih **Coba simulasi** untuk mencoba tanpa kamera. Tersedia alarm, kalibrasi ulang, pilihan kacamata gelap, dan ekspor riwayat CSV. Riwayat hanya tersimpan dalam memori tab (maksimal 500 kejadian), dan dihapus saat memulai sesi baru.

```sh
python3 -m http.server 8765 --directory web/dist
```

Buka http://localhost:8765. Kamera di hosting publik memerlukan HTTPS. Model dan runtime MediaPipe disertakan dalam `web/dist/vendor`; atribusi ada di `web/dist/THIRD_PARTY.txt`. Semua jalur aset relatif sehingga kompatibel dengan GitHub Pages.

## Python desktop

Gunakan Python 3.11:

```sh
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Tekan `c` untuk kalibrasi ulang dan `q` untuk keluar. Gunakan `main.py --eyes-obscured` untuk kacamata gelap; penilaian mata/PERCLOS akan dinonaktifkan. Konfigurasi kamera ada di `config.py`, log desktop ada di `logs/`.

## Deteksi dan perbaikan

- Kalibrasi baseline pribadi, median sampel, hysteresis mata, dan durasi berbasis waktu; kedipan singkat tidak memicu alarm mata tertutup lama.
- Python menolak beberapa wajah sekaligus. Mata terpotong atau lebar <12 piksel tidak dinilai; jarak sudut luar mata <30 piksel menghasilkan pembacaan wajah tidak valid.
- Pose Python diperiksa melalui reproyeksi, kedalaman positif, dan nilai finite. Error reproyeksi >12% jarak sudut luar mata ditolak.
- Status mata direset setelah jeda kamera >0,5 detik. Mulut terbuka ketika kepala pada pose ekstrem tidak dianggap menguap.
- Python dan browser memakai ambang bersama di `web/dist/rules.json` dan aturan keputusan yang diuji kesetaraannya. Estimasi pose Python memakai solvePnP, sedangkan browser memakai matriks MediaPipe; keduanya tidak dijamin menghasilkan sudut identik.
- Browser membatalkan sesi yang sedang memuat ketika tab disembunyikan, agar kamera tidak menyala terlambat di latar.

Default: menoleh >20° atau menunduk >18° selama 1 detik; kedua mata tertutup atau mulut terbuka selama 1,5 detik. PERCLOS memerlukan 20 detik pembacaan mata valid dalam jendela 60 detik.

## Pengujian

```sh
.venv/bin/python -m unittest discover -s tests -v
node --check web/dist/app.mjs
node --check web/dist/engine.mjs
```

Node.js dibutuhkan untuk uji kesetaraan aturan Python/JavaScript. Uji geometri menggunakan pose sintetis yang diketahui. Belum tersedia dataset pengemudi berlabel, sehingga peningkatan akurasi, precision/recall, atau penurunan alarm palsu pada kondisi nyata belum dapat diklaim. Lakukan pengujian saat kendaraan berhenti. Pantulan kacamata, cahaya buruk, kamera bergerak, atau kalibrasi sambil menoleh dapat memengaruhi hasil. Sistem ini merupakan indikator perilaku, bukan jaminan keselamatan.

## Publikasi

Lihat `DEPLOYMENT.md` untuk tautan publik. GitHub Pages menerbitkan cabang `gh-pages`, yang berisi isi `web/dist`. Setelah perubahan website, jalankan `git subtree push --prefix web/dist origin gh-pages`. Hosting statis menjalankan deteksi JavaScript di browser; aplikasi Python tetap dijalankan lokal. `.env`, kunci privat, log, backup, dan virtualenv dikecualikan dari repositori.

Referensi: [OpenCV solvePnP](https://docs.opencv.org/4.x/d5/d1f/calib3d_solvePnP.html) dan [MediaPipe Face Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/web_js).
