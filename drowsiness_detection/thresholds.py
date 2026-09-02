"""
thresholds.py
==============

Defines the raw numeric thresholds used by the drowsiness detector.

IMPORTANT: None of these values are medically validated. They are
reasonable starting points for a college prototype, chosen from common
values used in EAR/MAR-based drowsiness-detection demos. Tune them for
your own camera, lighting, and test subjects.

All duration values are in SECONDS (not frames), so the detector works
correctly regardless of camera frame rate.
"""

from dataclasses import dataclass


@dataclass
class Thresholds:
    """Raw thresholds for eye/mouth/head based drowsiness signals."""

    # --- Eye closure -----------------------------------------------------
    # Eye Aspect Ratio (EAR) below this value is treated as "eye closed"
    # for a single frame. Typical open eyes sit around 0.25-0.35; this
    # depends heavily on the facial_analysis module's calibration.
    ear_threshold: float = 0.21

    # How long (seconds) the eyes must remain continuously closed before
    # it counts as "prolonged closure" rather than a normal blink.
    # A typical human blink lasts ~0.1-0.4s, so this is set safely above
    # that.
    eye_closed_duration_threshold: float = 1.5

    # --- Mouth / yawning ---------------------------------------------------
    # Mouth Aspect Ratio (MAR) above this value is treated as "mouth open"
    # for a single frame.
    mar_threshold: float = 0.55

    # How long (seconds) the mouth must remain continuously open before it
    # counts as a "yawn" rather than talking/normal mouth movement.
    mouth_open_duration_threshold: float = 1.2

    # --- Head tilt (optional / weak signal) --------------------------------
    # Absolute head tilt angle (degrees) beyond which the head is
    # considered to be drooping/nodding off. This is treated as a weak,
    # optional contributor to the score, never sufficient on its own.
    head_tilt_threshold: float = 15.0

    # --- Scoring -------------------------------------------------------
    # Smoothed drowsiness_score (0.0-1.0) at/above which the driver is
    # considered DROWSY (before hysteresis/debouncing is applied).
    drowsiness_score_threshold: float = 0.5

    # --- Temporal smoothing / hysteresis --------------------------------
    # Size (seconds) of the rolling window used to smooth the raw
    # per-frame score, to reduce frame-to-frame noise.
    score_smoothing_window: float = 1.0

    # A state change (AWAKE -> DROWSY or DROWSY -> AWAKE) is only
    # confirmed once the *new* condition has held continuously for this
    # many seconds. This prevents rapid flickering between states.
    state_change_debounce: float = 1.0
