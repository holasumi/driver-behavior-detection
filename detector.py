"""Wrapper MediaPipe FaceMesh: dari satu frame -> metrik wajah (EAR, MAR, pose kepala)."""

from dataclasses import dataclass
from typing import Optional

import mediapipe as mp
import cv2
import numpy as np

import utils


@dataclass
class FaceMetrics:
    ear: float
    mar: float
    yaw: float
    pitch: float
    roll: float
    landmarks: list
    left_ear: float = 0.0
    right_ear: float = 0.0
    face_valid: bool = True
    eyes_valid: bool = True


class FaceMeshDetector:
    def __init__(self, max_faces=2, refine_landmarks=True, min_detection_confidence=0.7, min_tracking_confidence=0.7):
        self._mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=max_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process(self, frame_bgr) -> Optional[FaceMetrics]:
        h, w = frame_bgr.shape[:2]
        if h == 0 or w == 0:
            return None
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._mesh.process(rgb)
        if not result.multi_face_landmarks or len(result.multi_face_landmarks) != 1:
            return None

        face_landmarks = result.multi_face_landmarks[0]
        points = [(lm.x * w, lm.y * h) for lm in face_landmarks.landmark]
        if not np.isfinite(points).all():
            return None

        left_ear = utils.eye_aspect_ratio(points, utils.LEFT_EYE)
        right_ear = utils.eye_aspect_ratio(points, utils.RIGHT_EYE)
        ear = (left_ear + right_ear) / 2.0

        mar = utils.mouth_aspect_ratio(points)
        pitch, yaw, roll = utils.estimate_head_pose(points, frame_bgr.shape)

        return FaceMetrics(ear=ear, mar=mar, yaw=yaw, pitch=pitch, roll=roll, landmarks=points, left_ear=left_ear, right_ear=right_ear,
                           face_valid=all(0 <= points[i][0] < w and 0 <= points[i][1] < h for i in utils.POSE_LANDMARK_IDS),
                           eyes_valid=utils.eyes_are_measurable(points, w, h))

    def close(self):
        self._mesh.close()
