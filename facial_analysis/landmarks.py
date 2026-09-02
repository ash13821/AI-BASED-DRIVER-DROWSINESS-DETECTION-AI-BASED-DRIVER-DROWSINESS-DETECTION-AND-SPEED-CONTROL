"""
landmarks.py

Thin wrapper around MediaPipe Face Mesh responsible ONLY for turning an
OpenCV BGR frame into pixel-space landmark coordinates. It does not compute
any drowsiness-related features itself — that is calculations.py's job,
orchestrated by feature_extractor.py.

Isolating MediaPipe here means that if the landmark backend ever changes
(a different model, a different library version), only this file needs
to change.
"""

from typing import List, Optional, Tuple

import numpy as np

try:
    import mediapipe as mp
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "mediapipe is required for facial_analysis.landmarks. "
        "Install it with: pip install mediapipe"
    ) from exc

from .config import FaceMeshConfig

Point = Tuple[float, float]


class LandmarkDetector:
    """
    Wraps mediapipe.solutions.face_mesh.FaceMesh and exposes a simple
    detect() method that returns pixel-space (x, y) landmark points for
    the first detected face, or None if no face is found.
    """

    def __init__(self, config: Optional[FaceMeshConfig] = None) -> None:
        self._config = config or FaceMeshConfig()
        self._mp_face_mesh = mp.solutions.face_mesh
        self._face_mesh = self._mp_face_mesh.FaceMesh(
            static_image_mode=self._config.static_image_mode,
            max_num_faces=self._config.max_num_faces,
            refine_landmarks=self._config.refine_landmarks,
            min_detection_confidence=self._config.min_detection_confidence,
            min_tracking_confidence=self._config.min_tracking_confidence,
        )

    def detect(self, frame_bgr: np.ndarray) -> Optional[List[Point]]:
        """
        Run face mesh detection on a single BGR frame.

        Returns:
            A list of (x, y) pixel coordinates for all detected landmarks
            of the first face, or None if no face was detected or the
            frame is invalid.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return None

        height, width = frame_bgr.shape[:2]

        # MediaPipe expects RGB input.
        frame_rgb = frame_bgr[:, :, ::-1]
        results = self._face_mesh.process(frame_rgb)

        if not results.multi_face_landmarks:
            return None

        face_landmarks = results.multi_face_landmarks[0]

        points: List[Point] = [
            (landmark.x * width, landmark.y * height)
            for landmark in face_landmarks.landmark
        ]
        return points

    def close(self) -> None:
        """Release MediaPipe resources. Call when done with the detector."""
        self._face_mesh.close()

    def __enter__(self) -> "LandmarkDetector":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
