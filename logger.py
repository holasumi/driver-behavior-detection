"""Pencatatan kejadian (drowsy, yawn, distracted) ke file CSV untuk analisis lanjutan."""

import os
import csv
from datetime import datetime

import config


class EventLogger:
    def __init__(self):
        os.makedirs(config.LOG_DIR, exist_ok=True)
        self.path = os.path.join(config.LOG_DIR, config.LOG_FILE)
        is_new = not os.path.exists(self.path)
        self._file = open(self.path, "a", newline="")
        self._writer = csv.writer(self._file)
        if is_new:
            self._writer.writerow(["timestamp", "event", "ear", "mar", "yaw", "pitch"])

    def log(self, event, ear=None, mar=None, yaw=None, pitch=None):
        self._writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            event,
            round(ear, 3) if ear is not None else "",
            round(mar, 3) if mar is not None else "",
            round(yaw, 1) if yaw is not None else "",
            round(pitch, 1) if pitch is not None else "",
        ])
        self._file.flush()

    def close(self):
        self._file.close()
