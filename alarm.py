"""Alarm suara lintas platform, dijalankan di thread terpisah agar tidak memblokir video loop."""

import sys
import subprocess
import threading


def _beep_macos():
    subprocess.run(["afplay", "/System/Library/Sounds/Sosumi.aiff"], check=False)


def _beep_windows():
    import winsound
    winsound.Beep(2500, 700)


def _beep_linux():
    try:
        subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga"], check=False)
    except FileNotFoundError:
        print("\a", end="", flush=True)


def _play():
    if sys.platform == "darwin":
        _beep_macos()
    elif sys.platform.startswith("win"):
        _beep_windows()
    else:
        _beep_linux()


_last_thread = None


def play_alert_async():
    """Memicu bunyi alarm tanpa memblokir thread pemanggil (drop jika alarm sebelumnya masih bunyi)."""
    global _last_thread
    if _last_thread is not None and _last_thread.is_alive():
        return
    _last_thread = threading.Thread(target=_play, daemon=True)
    _last_thread.start()
