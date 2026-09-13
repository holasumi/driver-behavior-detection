# Validasi 13 September 2026

- 19 pengujian aturan dan geometri lulus: kedipan, kedua mata tertutup, durasi pada beberapa FPS, wajah hilang, jeda kamera, PERCLOS, kalibrasi, timestamp non-finite, pose ekstrem, dan kualitas geometri.
- Kesetaraan Python/JavaScript diuji pada 1.201 sampel metrik termasuk pose ekstrem dan mata tidak valid.
- Geometri sintetis: yaw -30°, 0°, +30° dipulihkan dengan toleransi 0,001°. Landmark rusak dan mata terlalu kecil ditolak.
- Sintaks kedua modul JavaScript, referensi aset HTML, dan pemindaian pola kredensial aplikasi lulus.
- Pratinjau HTTP lokal merespons 200. Aset model/WASM dipulihkan dari repositori website sebelumnya agar tersedia sebagai berkas nyata, bukan placeholder iCloud.
- Tidak dilakukan pengujian interaksi/visual browser baru atau kamera pengemudi nyata pada pembaruan ini.

Belum ada dataset pengemudi berlabel. Angka peningkatan akurasi, precision/recall, dan penurunan alarm palsu tidak dapat diklaim. Batas ukuran mata dan error reproyeksi merupakan heuristik awal yang perlu dievaluasi pada kondisi kamera sebenarnya.

## Uji penerimaan berikutnya

Saat kendaraan berhenti, kalibrasi lalu uji menoleh, berkedip, mata tertutup >1,5 detik, berbicara, menguap, dan wajah keluar bingkai. Ulangi dengan beberapa orang, kondisi cahaya, dan kacamata. Bandingkan waktu kejadian nyata dengan CSV; gunakan data berbeda untuk menyetel ambang dan mengukur akurasi.
