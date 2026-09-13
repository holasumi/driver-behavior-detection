import math
import unittest

import cv2
import numpy as np

import utils


class GeometryTests(unittest.TestCase):
    def points(self, rotation=(0., 0., 0.)):
        camera = np.array([[640., 0., 320.], [0., 640., 240.], [0., 0., 1.]])
        projected, _ = cv2.projectPoints(utils.MODEL_POINTS_3D, np.array(rotation),
                                        np.array([0., 0., 600.]), camera, np.zeros(4))
        points = np.zeros((468, 2))
        points[utils.POSE_LANDMARK_IDS] = projected.reshape(-1, 2)
        return points

    def test_known_pose(self):
        for degrees in (-30, 0, 30):
            pitch, yaw, roll = utils.estimate_head_pose(
                self.points((0., math.radians(degrees), 0.)), (480, 640, 3))
            self.assertAlmostEqual(yaw, degrees, places=3)
            self.assertAlmostEqual(pitch, 0., places=3)
            self.assertAlmostEqual(roll, 0., places=3)

    def test_distorted_landmarks_rejected(self):
        points = self.points()
        points[152] += [200, -180]
        self.assertTrue(all(math.isnan(x) for x in utils.estimate_head_pose(points, (480, 640, 3))))

    def test_collapsed_geometry_is_unknown(self):
        points = np.zeros((468, 2))
        self.assertTrue(math.isnan(utils.eye_aspect_ratio(points, utils.LEFT_EYE)))
        self.assertTrue(math.isnan(utils.mouth_aspect_ratio(points)))
        self.assertFalse(utils.eyes_are_measurable(points, 640, 480))
        self.assertTrue(all(math.isnan(x) for x in utils.estimate_head_pose(points, (480, 640, 3))))

    def test_tiny_eyes_rejected(self):
        points = np.full((468, 2), 100.)
        points[263] = [105, 100]
        points[133] = [105, 100]
        self.assertFalse(utils.eyes_are_measurable(points, 640, 480))
