"""
config.py
==========

Top-level configuration for the DrowsinessDetector.

Wraps the raw `Thresholds` (thresholds.py) together with the scoring
weights used to combine multiple signals into one drowsiness_score, and a
couple of misc settings. Keeping this separate from `thresholds.py` lets
you change *what counts as closed/open/tilted* independently from *how
much each signal contributes to the final score*.

All values can be overridden either by constructing the dataclasses
directly or by passing a partial dict to `DetectorConfig.from_dict`.
"""

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Optional

from .thresholds import Thresholds


@dataclass
class ScoreWeights:
    """
    Relative contribution of each signal to the raw drowsiness score.

    The final raw score is clipped to [0.0, 1.0], so weights do not need
    to sum to exactly 1.0 -- they just express relative importance.
    Prolonged/confirmed signals are weighted higher than instantaneous
    ones, per the "do not classify from a single frame" requirement.
    """

    eye_closed_instant: float = 0.10      # single-frame eyes-closed (weak)
    eye_closed_prolonged: float = 0.55    # closure past duration threshold (strong)
    yawn_instant: float = 0.05            # single-frame mouth-open (weak)
    yawn_prolonged: float = 0.25          # yawn past duration threshold
    head_tilt: float = 0.10               # optional, weak on its own


@dataclass
class DetectorConfig:
    """Full configuration bundle consumed by DrowsinessDetector."""

    thresholds: Thresholds = field(default_factory=Thresholds)
    weights: ScoreWeights = field(default_factory=ScoreWeights)

    # If avg_ear is missing from input features, compute it as the mean of
    # left_ear/right_ear when both are present.
    derive_avg_ear_if_missing: bool = True

    # Assumed frames-per-second, used only as a fallback when the caller
    # does not supply timestamps to `update()`. Real deployments should
    # always pass real timestamps for accurate temporal behaviour.
    assumed_fps: float = 15.0

    @classmethod
    def from_dict(cls, overrides: Optional[Dict[str, Any]] = None) -> "DetectorConfig":
        """
        Build a DetectorConfig from a flat dict of overrides, e.g.:

            DetectorConfig.from_dict({
                "ear_threshold": 0.18,
                "eye_closed_duration_threshold": 2.0,
                "eye_closed_prolonged_weight": 0.6,
            })

        Unknown keys are ignored so callers can pass a superset of
        options without raising errors.
        """
        overrides = overrides or {}
        config = cls()

        threshold_fields = {f for f in Thresholds.__dataclass_fields__}
        weight_field_map = {
            "eye_closed_instant_weight": "eye_closed_instant",
            "eye_closed_prolonged_weight": "eye_closed_prolonged",
            "yawn_instant_weight": "yawn_instant",
            "yawn_prolonged_weight": "yawn_prolonged",
            "head_tilt_weight": "head_tilt",
        }

        threshold_updates = {k: v for k, v in overrides.items() if k in threshold_fields}
        if threshold_updates:
            config.thresholds = replace(config.thresholds, **threshold_updates)

        weight_updates = {
            weight_field_map[k]: v for k, v in overrides.items() if k in weight_field_map
        }
        if weight_updates:
            config.weights = replace(config.weights, **weight_updates)

        if "derive_avg_ear_if_missing" in overrides:
            config.derive_avg_ear_if_missing = overrides["derive_avg_ear_if_missing"]
        if "assumed_fps" in overrides:
            config.assumed_fps = overrides["assumed_fps"]

        return config
