"""
calculations.py

Pure numerical calculations used to turn facial landmark coordinates into
drowsiness-related features (EAR, MAR, head tilt, openness metrics).

These functions do not know about MediaPipe, OpenCV, or the camera. They
operate on plain (x, y) coordinate lists so they stay easy to unit test and
easy to reuse if the landmark source ever changes.
"""

import math
from typing import List, Optional, Tuple

import numpy as np

Point = Tuple[float, float]


def euclidean_distance(p1: Point, p2: Point) -> float:
    """Return the Euclidean distance between two 2D points."""
    return float(np.linalg.norm(np.array(p1) - np.array(p2)))


def eye_aspect_ratio(eye_points: List[Point]) -> Optional[float]:
    """
    Calculate the Eye Aspect Ratio (EAR) for a single eye.

    Expects exactly 6 (x, y) points in the order:
        [p1, p2, p3, p4, p5, p6]
    where p1/p4 are the horizontal corners of the eye and
    p2/p3, p5/p6 are the vertical top/bottom pairs, following the
    standard formulation from Soukupova & Cech (2016):

        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

    Returns None if the points are degenerate (e.g. zero width),
    so callers never divide by zero.
    """
    if len(eye_points) != 6:
        return None

    p1, p2, p3, p4, p5, p6 = eye_points

    vertical_1 = euclidean_distance(p2, p6)
    vertical_2 = euclidean_distance(p3, p5)
    horizontal = euclidean_distance(p1, p4)

    if horizontal <= 1e-6:
        return None

    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return float(ear)


def mouth_aspect_ratio(mouth_points: List[Point]) -> Optional[float]:
    """
    Calculate the Mouth Aspect Ratio (MAR).

    Expects exactly 6 (x, y) points in the order:
        [left_corner, top_outer, top_inner, right_corner, bottom_inner, bottom_outer]

    MAR = (||top_outer-bottom_outer|| + ||top_inner-bottom_inner||)
          / (2 * ||left_corner-right_corner||)

    Returns None on degenerate input.
    """
    if len(mouth_points) != 6:
        return None

    left_corner, top_outer, top_inner, right_corner, bottom_inner, bottom_outer = mouth_points

    vertical_1 = euclidean_distance(top_outer, bottom_outer)
    vertical_2 = euclidean_distance(top_inner, bottom_inner)
    horizontal = euclidean_distance(left_corner, right_corner)

    if horizontal <= 1e-6:
        return None

    mar = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return float(mar)


def eye_openness_from_ear(avg_ear: Optional[float], max_expected_ear: float = 0.4) -> Optional[float]:
    """
    Convert an average EAR value into a normalized "openness" score in the
    range [0.0, 1.0], where 0.0 is fully closed and 1.0 is fully open.

    This is a simple linear scaling against a typical maximum EAR for open
    eyes. It is a convenience metric for consumers that want a normalized
    value rather than a raw ratio; it is not a substitute for the raw EAR.
    """
    if avg_ear is None:
        return None

    openness = avg_ear / max_expected_ear
    return float(min(max(openness, 0.0), 1.0))


def head_tilt_angle(left_eye_outer: Point, right_eye_outer: Point) -> Optional[float]:
    """
    Estimate head tilt (roll) in degrees using the line between the outer
    corners of the two eyes relative to horizontal.

    A positive value indicates the head is tilted one way, negative the
    other; the sign convention follows standard image coordinates
    (y increases downward).

    This is a lightweight 2D approximation, not a full 3D head-pose
    solve (pitch/yaw). It is useful for detecting head nodding/tilting
    associated with drowsiness without requiring camera calibration.
    """
    if left_eye_outer is None or right_eye_outer is None:
        return None

    dx = right_eye_outer[0] - left_eye_outer[0]
    dy = right_eye_outer[1] - left_eye_outer[1]

    if dx == 0 and dy == 0:
        return None

    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)
    return float(angle_deg)
