"""
detector.py
============

Public interface of the drowsiness_detection module.

    from drowsiness_detection.detector import DrowsinessDetector

    detector = DrowsinessDetector()
    result = detector.update(features)   # features from facial_analysis/

`DrowsinessDetector` is intentionally the ONLY class other modules need
to import. It owns a `StateTracker` (temporal history) and a
`DetectorConfig` (thresholds + weights), and exposes a single `update()`
method per frame.

Responsibility boundary (see project README):
  - Consumes numeric facial features. Never touches the camera.
  - Never re-computes facial landmarks. Never calls brake()/slow_down().
  - Only decides AWAKE / DROWSY / UNKNOWN + a drowsiness score.
"""

import time
from typing import Any, Dict, Optional

from .config import DetectorConfig
from .state_tracker import StateTracker


class DrowsinessDetector:
    """
    Stateful, per-driver drowsiness detector.

    One instance should be kept alive for the duration of a driving
    session (it tracks history across calls). Create a new instance per
    driver/session if you need independent tracking.
    """

    VALID_STATES = ("AWAKE", "DROWSY", "UNKNOWN")

    def __init__(self, config: Optional[DetectorConfig] = None) -> None:
        self.config = config or DetectorConfig()
        self._tracker = StateTracker(
            smoothing_window_seconds=self.config.thresholds.score_smoothing_window,
            debounce_seconds=self.config.thresholds.state_change_debounce,
        )

    # -- public API -----------------------------------------------------------

    def update(
        self, features: Dict[str, Any], timestamp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process one frame's worth of facial features and return the
        current driver state.

        Parameters
        ----------
        features:
            Dict produced by `facial_analysis/`, expected to contain
            (all optional except `face_detected`):
                face_detected: bool
                left_ear, right_ear, avg_ear: float
                mar: float
                eye_openness: float   (currently informational only)
                eyes_closed: bool
                mouth_open: bool
                head_tilt: float (degrees)
        timestamp:
            Seconds (e.g. `time.time()` or a video PTS). If omitted, the
            wall clock is used. Passing explicit timestamps is strongly
            recommended for reproducible tests and for offline/replayed
            video processing.

        Returns
        -------
        dict with keys: state, drowsiness_score, confidence, reason.
        """
        ts = time.time() if timestamp is None else float(timestamp)

        if not features.get("face_detected", False):
            self._tracker.reset()
            return {
                "state": "UNKNOWN",
                "drowsiness_score": 0.0,
                "confidence": 0.0,
                "reason": "face_not_detected",
            }

        avg_ear = self._resolve_avg_ear(features)
        mar = features.get("mar")
        head_tilt = float(features.get("head_tilt", 0.0) or 0.0)

        eyes_closed_flag = self._resolve_eyes_closed(features, avg_ear)
        mouth_open_flag = self._resolve_mouth_open(features, mar)

        eye_closed_duration = self._tracker.update_eye_closure(eyes_closed_flag, ts)
        mouth_open_duration = self._tracker.update_mouth_open(mouth_open_flag, ts)

        raw_score = self._compute_raw_score(
            eyes_closed_flag=eyes_closed_flag,
            eye_closed_duration=eye_closed_duration,
            mouth_open_flag=mouth_open_flag,
            mouth_open_duration=mouth_open_duration,
            head_tilt=head_tilt,
        )

        smoothed_score = self._tracker.push_score(raw_score, ts)

        thresholds = self.config.thresholds
        candidate_state = (
            "DROWSY" if smoothed_score >= thresholds.drowsiness_score_threshold else "AWAKE"
        )
        confirmed_state = self._tracker.resolve_state(candidate_state, ts)

        confidence = self._compute_confidence(smoothed_score)
        reason = self._compute_reason(
            confirmed_state=confirmed_state,
            eye_closed_duration=eye_closed_duration,
            mouth_open_duration=mouth_open_duration,
            head_tilt=head_tilt,
        )

        return {
            "state": confirmed_state,
            "drowsiness_score": round(smoothed_score, 3),
            "confidence": round(confidence, 3),
            "reason": reason,
        }

    def reset(self) -> None:
        """Reset all temporal state, e.g. at the start of a new trip."""
        self._tracker = StateTracker(
            smoothing_window_seconds=self.config.thresholds.score_smoothing_window,
            debounce_seconds=self.config.thresholds.state_change_debounce,
        )

    # -- feature resolution helpers --------------------------------------------

    def _resolve_avg_ear(self, features: Dict[str, Any]) -> Optional[float]:
        avg_ear = features.get("avg_ear")
        if avg_ear is not None:
            return float(avg_ear)

        if self.config.derive_avg_ear_if_missing:
            left = features.get("left_ear")
            right = features.get("right_ear")
            if left is not None and right is not None:
                return (float(left) + float(right)) / 2.0

        return None

    def _resolve_eyes_closed(self, features: Dict[str, Any], avg_ear: Optional[float]) -> bool:
        # Prefer an explicit upstream flag, but always OR it with our own
        # EAR-threshold check so the detector is robust even if
        # facial_analysis doesn't set `eyes_closed`.
        explicit_flag = bool(features.get("eyes_closed", False))
        ear_flag = avg_ear is not None and avg_ear < self.config.thresholds.ear_threshold
        return explicit_flag or ear_flag

    def _resolve_mouth_open(self, features: Dict[str, Any], mar: Optional[float]) -> bool:
        explicit_flag = bool(features.get("mouth_open", False))
        mar_flag = mar is not None and float(mar) > self.config.thresholds.mar_threshold
        return explicit_flag or mar_flag

    # -- scoring -----------------------------------------------------------

    @staticmethod
    def _ramp_factor(duration: float, threshold: float) -> float:
        """
        0.0 below `threshold`. Once `duration` reaches `threshold`, ramps
        from 0.6 up to 1.0 as duration grows from 1x to 2x the threshold.
        This rewards *sustained* closure/yawning more than just barely
        crossing the line, without needing a second hard threshold.
        """
        if threshold <= 0 or duration < threshold:
            return 0.0
        ramp = min((duration - threshold) / threshold, 1.0)
        return 0.6 + 0.4 * ramp

    def _compute_raw_score(
        self,
        *,
        eyes_closed_flag: bool,
        eye_closed_duration: float,
        mouth_open_flag: bool,
        mouth_open_duration: float,
        head_tilt: float,
    ) -> float:
        weights = self.config.weights
        thresholds = self.config.thresholds

        score = 0.0

        if eyes_closed_flag:
            score += weights.eye_closed_instant
        score += weights.eye_closed_prolonged * self._ramp_factor(
            eye_closed_duration, thresholds.eye_closed_duration_threshold
        )

        if mouth_open_flag:
            score += weights.yawn_instant
        score += weights.yawn_prolonged * self._ramp_factor(
            mouth_open_duration, thresholds.mouth_open_duration_threshold
        )

        if abs(head_tilt) > thresholds.head_tilt_threshold:
            tilt_factor = min(
                abs(head_tilt) / (thresholds.head_tilt_threshold * 2.0), 1.0
            )
            score += weights.head_tilt * tilt_factor

        return max(0.0, min(1.0, score))

    def _compute_confidence(self, smoothed_score: float) -> float:
        """
        Simple confidence heuristic: the further the smoothed score sits
        from the decision threshold, the more confident we are in the
        classification. This is NOT a statistical/calibrated confidence
        -- it is a rough, explainable signal for downstream consumers.
        """
        threshold = self.config.thresholds.drowsiness_score_threshold
        distance = abs(smoothed_score - threshold)
        max_distance = max(threshold, 1.0 - threshold, 1e-6)
        return 0.5 + 0.5 * min(distance / max_distance, 1.0)

    def _compute_reason(
        self,
        *,
        confirmed_state: str,
        eye_closed_duration: float,
        mouth_open_duration: float,
        head_tilt: float,
    ) -> Optional[str]:
        if confirmed_state != "DROWSY":
            return None

        thresholds = self.config.thresholds
        eye_flag = eye_closed_duration >= thresholds.eye_closed_duration_threshold
        mouth_flag = mouth_open_duration >= thresholds.mouth_open_duration_threshold
        tilt_flag = abs(head_tilt) > thresholds.head_tilt_threshold

        if eye_flag and mouth_flag:
            return "combined_indicators"
        if eye_flag:
            return "prolonged_eye_closure"
        if mouth_flag:
            return "yawning"
        if tilt_flag:
            return "head_tilt"
        return "elevated_drowsiness_score"
