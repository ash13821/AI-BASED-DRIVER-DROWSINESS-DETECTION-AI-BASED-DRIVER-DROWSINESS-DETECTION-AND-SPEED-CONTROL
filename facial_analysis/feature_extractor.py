"""
feature_extractor.py

Main integration point of the facial_analysis module.

This is the ONLY file other modules (specifically drowsiness_detection)
should need to import from:

    from facial_analysis.feature_extractor import FacialFeatureExtractor

Responsibility boundary (see project spec):
    Video frame -> Face landmarks -> Numerical facial features

This module does NOT decide whether the driver is drowsy. It only
measures and returns structured features. Temporal/decision logic
(e.g. "eyes closed for 2 seconds = drowsy") belongs downstream in
drowsiness_detection/.
"""

from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np

from . import config as cfg
from .calculations import (
    eye_aspect_ratio,
    eye_openness_from_ear,
    head_tilt_angle,
    mouth_aspect_ratio,
)
from .landmarks import LandmarkDetector


@dataclass
class FacialFeatures:
    """
    Structured output of the facial_analysis module.

    This is the exact contract consumed by drowsiness_detection/.
    Field names and types are intentionally stable; new fields should be
    appended rather than existing ones renamed, so downstream code does
    not break.
    """

    face_detected: bool
    left_ear: Optional[float] = None
    right_ear: Optional[float] = None
    avg_ear: Optional[float] = None
    mar: Optional[float] = None
    eye_openness: Optional[float] = None
    eyes_closed: Optional[bool] = None
    mouth_open: Optional[bool] = None
    head_tilt: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to a plain dictionary, useful for logging/JSON/IPC."""
        return asdict(self)


def _empty_features() -> FacialFeatures:
    """Return the safe 'no face detected' feature set (all None)."""
    return FacialFeatures(face_detected=False)


class FacialFeatureExtractor:
    """
    Extracts numerical drowsiness-related facial features from a single
    camera frame.

    Usage:
        extractor = FacialFeatureExtractor()
        features = extractor.extract(frame)   # frame = OpenCV BGR image
        drowsiness_detection_module.analyze(features.to_dict())

    This class deliberately does NOT read from the camera itself in normal
    operation — it only processes frames handed to it by the camera
    module. A standalone webcam test mode is provided separately in
    test_camera.py for independent development/testing.
    """

    def __init__(self, extractor_config: Optional[cfg.ExtractorConfig] = None) -> None:
        self._config = extractor_config or cfg.ExtractorConfig()
        self._detector = LandmarkDetector(self._config.face_mesh)

    def extract(self, frame: np.ndarray) -> FacialFeatures:
        """
        Extract facial features from a single frame.

        Args:
            frame: An OpenCV BGR image (as produced by cv2.VideoCapture
                   or handed off from the camera/ module).

        Returns:
            A FacialFeatures instance. If no face is detected, or the
            frame is invalid, all measurement fields are None and
            face_detected is False. This method never raises for the
            "no face" case — it is safe to call on every frame.
        """
        try:
            landmarks = self._detector.detect(frame)
        except Exception:
            # Defensive: a malformed frame should not crash the pipeline.
            # The camera module may occasionally hand off a bad frame
            # (partial read, corrupt buffer, etc.) and this module must
            # degrade gracefully rather than propagate the exception.
            return _empty_features()

        if landmarks is None:
            return _empty_features()

        left_eye_pts = [landmarks[i] for i in cfg.LEFT_EYE_INDICES]
        right_eye_pts = [landmarks[i] for i in cfg.RIGHT_EYE_INDICES]
        mouth_pts = [landmarks[i] for i in cfg.MOUTH_INDICES]

        left_ear = eye_aspect_ratio(left_eye_pts)
        right_ear = eye_aspect_ratio(right_eye_pts)

        avg_ear: Optional[float] = None
        if left_ear is not None and right_ear is not None:
            avg_ear = (left_ear + right_ear) / 2.0

        mar = mouth_aspect_ratio(mouth_pts)
        eye_openness = eye_openness_from_ear(avg_ear)

        thresholds = self._config.thresholds
        eyes_closed = (
            avg_ear is not None and avg_ear < thresholds.ear_closed_threshold
        )
        mouth_open = (
            mar is not None and mar > thresholds.mar_open_threshold
        )

        # Head-tilt uses outer eye corners, which are the first point of
        # each eye list in our landmark ordering (see config.py).
        left_outer = landmarks[cfg.HEAD_POSE_INDICES[2]]
        right_outer = landmarks[cfg.HEAD_POSE_INDICES[3]]
        tilt = head_tilt_angle(left_outer, right_outer)

        return FacialFeatures(
            face_detected=True,
            left_ear=left_ear,
            right_ear=right_ear,
            avg_ear=avg_ear,
            mar=mar,
            eye_openness=eye_openness,
            eyes_closed=eyes_closed,
            mouth_open=mouth_open,
            head_tilt=tilt,
        )

    def close(self) -> None:
        """Release underlying MediaPipe resources."""
        self._detector.close()

    def __enter__(self) -> "FacialFeatureExtractor":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
