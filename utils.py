from functools import lru_cache

import numpy as np
import cv2


LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
MOUTH = {"top": 13, "bottom": 14, "left": 78, "right": 308}


POSE_LANDMARK_IDS = [1, 152, 33, 263, 61, 291]
MODEL_POINTS_3D = np.array([
    (0.0, 0.0, 0.0),
    (0.0, 63.6, 12.5),
    (-43.3, -32.7, 26.0),
    (43.3, -32.7, 26.0),
    (-28.9, 28.9, 24.1),
    (28.9, 28.9, 24.1),
], dtype=np.float64)


def _dist(a, b):
    return float(np.linalg.norm(np.array(a) - np.array(b)))


def eye_aspect_ratio(landmarks, indices):
    p1, p2, p3, p4, p5, p6 = [landmarks[i] for i in indices]
    vertical = _dist(p2, p6) + _dist(p3, p5)
    horizontal = 2.0 * _dist(p1, p4)
    if horizontal == 0:
        return float('nan')
    return vertical / horizontal


def mouth_aspect_ratio(landmarks):
    top = landmarks[MOUTH["top"]]
    bottom = landmarks[MOUTH["bottom"]]
    left = landmarks[MOUTH["left"]]
    right = landmarks[MOUTH["right"]]
    horizontal = _dist(left, right)
    if horizontal == 0:
        return float('nan')
    return _dist(top, bottom) / horizontal


def eyes_are_measurable(points, width, height):
    return all(
        _dist(points[ids[0]], points[ids[3]]) >= 12
        and all(0 <= points[i][0] < width and 0 <= points[i][1] < height for i in ids)
        for ids in (LEFT_EYE, RIGHT_EYE)
    )


@lru_cache(maxsize=4)
def _camera_parameters(h, w):
    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1],
    ], dtype=np.float64)
    dist_coeffs = np.zeros((4, 1))
    camera_matrix.flags.writeable = False
    dist_coeffs.flags.writeable = False
    return camera_matrix, dist_coeffs


def estimate_head_pose(landmarks, frame_shape):
    h, w = frame_shape[:2]
    image_points = np.array([landmarks[i] for i in POSE_LANDMARK_IDS], dtype=np.float64)
    invalid = (float('nan'),) * 3
    eye_span = _dist(image_points[2], image_points[3])
    if not np.isfinite(image_points).all() or eye_span < 30:
        return invalid
    camera_matrix, dist_coeffs = _camera_parameters(h, w)

    try:
        success, rotation_vec, translation_vec = cv2.solvePnP(
            MODEL_POINTS_3D, image_points, camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
    except cv2.error:
        return invalid
    if not success or not np.isfinite(rotation_vec).all() or not np.isfinite(translation_vec).all():
        return invalid
    rotation_mat, _ = cv2.Rodrigues(rotation_vec)
    depths = (rotation_mat @ MODEL_POINTS_3D.T + translation_vec)[2]
    projected, _ = cv2.projectPoints(MODEL_POINTS_3D, rotation_vec, translation_vec, camera_matrix, dist_coeffs)
    error = np.sqrt(np.mean(np.sum((projected.reshape(-1, 2) - image_points) ** 2, axis=1)))
    if np.any(depths <= 0) or error / eye_span > 0.12:
        return invalid

    pose_mat = np.hstack((rotation_mat, np.zeros((3, 1))))
    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
    pitch, yaw, roll = [float(a) for a in euler_angles.flatten()]
    return pitch, yaw, roll
