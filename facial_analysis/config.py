"""
config.py

Central configuration for the facial_analysis module.

Holds MediaPipe Face Mesh landmark indices used for EAR/MAR calculations
and tunable thresholds. Keeping these in one place makes it easy to add
new features later without touching calculation logic.
"""

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# MediaPipe Face Mesh landmark indices
# ---------------------------------------------------------------------------
# MediaPipe Face Mesh produces 468 (or 478 with iris) landmarks per face.
# The indices below pick out the points needed for EAR / MAR / head-tilt
# calculations. Order matters: each list is arranged so that calculations.py
# can consume it as [p1, p2, p3, p4, p5, p6] following the standard
# 6-point EAR formulation (Soukupova & Cech, 2016).

# Left eye (as seen from the camera, i.e. the driver's right eye)
LEFT_EYE_INDICES: List[int] = [33, 160, 158, 133, 153, 144]

# Right eye (as seen from the camera, i.e. the driver's left eye)
RIGHT_EYE_INDICES: List[int] = [362, 385, 387, 263, 373, 380]

# Mouth points used for the Mouth Aspect Ratio (outer lip contour)
# Order: [left corner, top-outer, top-inner-ish, right corner, bottom-inner-ish, bottom-outer]
MOUTH_INDICES: List[int] = [61, 291, 39, 181, 0, 17]

# Points used for a lightweight head-tilt / pose estimate.
# Nose tip, chin, left eye outer corner, right eye outer corner,
# left mouth corner, right mouth corner.
HEAD_POSE_INDICES: List[int] = [1, 152, 33, 263, 61, 291]


@dataclass
class FaceMeshConfig:
    """Configuration for the underlying MediaPipe Face Mesh model."""

    static_image_mode: bool = False
    max_num_faces: int = 1
    refine_landmarks: bool = True  # enables iris landmarks, improves eye accuracy
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5


@dataclass
class FeatureThresholds:
    """
    Thresholds used only to derive simple boolean flags (eyes_closed,
    mouth_open) that describe the CURRENT frame's raw measurement.

    IMPORTANT: These are NOT drowsiness thresholds. They do not determine
    whether the driver is drowsy — they only describe whether, in this
    single frame, the eyes/mouth appear closed/open. Temporal reasoning
    (e.g. "eyes closed for N consecutive frames") belongs in the
    drowsiness_detection module, not here.
    """

    ear_closed_threshold: float = 0.21
    mar_open_threshold: float = 0.45


@dataclass
class ExtractorConfig:
    """Top-level configuration bundle passed into FacialFeatureExtractor."""

    face_mesh: FaceMeshConfig = field(default_factory=FaceMeshConfig)
    thresholds: FeatureThresholds = field(default_factory=FeatureThresholds)
