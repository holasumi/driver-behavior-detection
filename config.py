"""Konfigurasi ambang batas & parameter deteksi.

Ubah nilai di sini untuk menyesuaikan sensitivitas tanpa menyentuh logika utama.
"""

CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Ambang perilaku dipakai bersama Python dan browser:
# web/dist/rules.json (detik, kalibrasi, yaw/pitch, PERCLOS).

# --- Logging ---
LOG_DIR = "logs"
LOG_FILE = "driver_events.csv"
