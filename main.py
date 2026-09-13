"""Driver Behavior Detection — deteksi kantuk, menguap, dan distraksi (menoleh/menunduk) via webcam.

Jalankan:
    python main.py

Tekan 'q' untuk keluar.
"""

import time
import argparse

import cv2

import config
import alarm
from detector import FaceMeshDetector
from logger import EventLogger


from state import DriverState


def draw_hud(frame, metrics, result, status_text, status_color):
    y = 24
    for label in (
        f"EAR: {metrics.ear:.2f}" if metrics else "EAR: --",
        f"MAR: {metrics.mar:.2f}" if metrics else "MAR: --",
        f"Yaw/Pitch: {metrics.yaw:.0f}/{metrics.pitch:.0f}" if metrics else "Yaw/Pitch: --",
        f"PERCLOS: {result['perclos'] * 100:.0f}%" if result['perclos'] is not None else "PERCLOS: --",
    ):
        cv2.putText(frame, label, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        y += 22

    cv2.putText(frame, status_text, (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, status_color, 2, cv2.LINE_AA)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--eyes-obscured', action='store_true', help='Kacamata gelap: hanya pantau pose kepala dan mulut')
    args = parser.parse_args()
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        print("Tidak bisa membuka kamera. Cek CAMERA_INDEX di config.py.")
        return

    face_detector = FaceMeshDetector()
    state = DriverState(eyes_obscured=args.eyes_obscured)
    event_logger = EventLogger()

    print("Driver Behavior Detection berjalan. Tekan 'q' untuk keluar.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Gagal membaca frame dari kamera.")
                break

            # Estimate geometry before any cosmetic mirroring.
            metrics = face_detector.process(frame)
            result = state.update(metrics)
            labels = {
                "calibration": f"Lihat lurus, buka mata, tutup mulut: {result['progress']:.0%}",
                "no_face": "Wajah tidak terbaca",
                "eyes_unknown": "Mata tidak dapat dinilai",
                "normal": "Tidak ada peringatan",
                "drowsy": "MATA TERTUTUP LAMA! Beristirahatlah",
                "distracted": "Fokus ke jalan!",
                "yawn": "Mulut terbuka lama / kemungkinan menguap",
                "fatigue": "Indikasi lelah (PERCLOS tinggi)",
            }
            status_text = labels[result['status']]
            status_color = (0, 200, 0) if result['status'] == 'normal' else (0, 165, 255)
            if result['status'] in ('drowsy', 'distracted'):
                status_color = (0, 0, 255)
                alarm.play_alert_async()
            for event in result['events']:
                event_logger.log('drowsy_start' if event == 'drowsy' else event,
                                 ear=metrics.ear, mar=metrics.mar,
                                 yaw=result['metrics']['yaw'], pitch=result['metrics']['pitch'])
            draw_hud(frame, metrics, result, status_text, status_color)
            cv2.imshow("Driver Behavior Detection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            if key == ord('c'):
                state = DriverState(eyes_obscured=args.eyes_obscured)
    finally:
        cap.release()
        cv2.destroyAllWindows()
        face_detector.close()
        event_logger.close()


if __name__ == "__main__":
    main()
