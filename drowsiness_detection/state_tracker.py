"""
state_tracker.py
==================

Holds all the *temporal* state the detector needs across calls to
`update()`: how long eyes/mouth have been continuously closed/open, a
rolling window of recent scores for smoothing, and debounced state
transitions so the reported driver state doesn't flicker frame to frame.

This module has no knowledge of EAR/MAR semantics -- it only tracks
durations and scores that `detector.py` gives it. That keeps the
"what counts as closed" logic (thresholds) separate from "how long has
it been true" logic (this file).
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional, Tuple


@dataclass
class ConditionTimer:
    """
    Tracks how long a boolean condition (e.g. 'eyes closed') has been
    continuously true, using wall-clock/video timestamps rather than
    frame counts, so behaviour is independent of camera FPS.
    """

    active_since: Optional[float] = None
    last_timestamp: Optional[float] = None

    def update(self, condition: bool, timestamp: float) -> float:
        """
        Update the timer with the latest condition value and timestamp.

        Returns the current continuous-duration (seconds) the condition
        has been True. Returns 0.0 if the condition is False, or if time
        moved backwards/stayed the same in a way that would make the
        duration meaningless (treated as a reset, not an error, since
        simulated/test timestamps may not always be strictly increasing
        across unrelated test cases).
        """
        if not condition:
            self.active_since = None
            self.last_timestamp = timestamp
            return 0.0

        if self.active_since is None or (
            self.last_timestamp is not None and timestamp < self.last_timestamp
        ):
            # Condition just became true, or clock went backwards -> restart.
            self.active_since = timestamp

        self.last_timestamp = timestamp
        return max(0.0, timestamp - self.active_since)


class StateTracker:
    """
    Aggregates per-frame signals into smoothed, debounced driver state.
    """

    def __init__(self, smoothing_window_seconds: float, debounce_seconds: float) -> None:
        self.smoothing_window_seconds = smoothing_window_seconds
        self.debounce_seconds = debounce_seconds

        self.eye_closed_timer = ConditionTimer()
        self.mouth_open_timer = ConditionTimer()

        # Rolling (timestamp, score) history for smoothing.
        self._score_history: Deque[Tuple[float, float]] = deque()

        # Confirmed (externally reported) state and how long the *pending*
        # candidate state has been consistently requested.
        self.confirmed_state: str = "AWAKE"
        self._pending_state: Optional[str] = None
        self._pending_since: Optional[float] = None

    # -- duration tracking -------------------------------------------------

    def update_eye_closure(self, eyes_closed: bool, timestamp: float) -> float:
        """Return continuous eye-closure duration in seconds."""
        return self.eye_closed_timer.update(eyes_closed, timestamp)

    def update_mouth_open(self, mouth_open: bool, timestamp: float) -> float:
        """Return continuous mouth-open duration in seconds."""
        return self.mouth_open_timer.update(mouth_open, timestamp)

    # -- score smoothing -----------------------------------------------------

    def push_score(self, raw_score: float, timestamp: float) -> float:
        """
        Add a raw score to the rolling window and return the smoothed
        (moving-average) score over `smoothing_window_seconds`.
        """
        self._score_history.append((timestamp, raw_score))

        cutoff = timestamp - self.smoothing_window_seconds
        while self._score_history and self._score_history[0][0] < cutoff:
            self._score_history.popleft()

        if not self._score_history:
            return raw_score

        total = sum(score for _, score in self._score_history)
        return total / len(self._score_history)

    # -- debounced state machine --------------------------------------------

    def resolve_state(self, candidate_state: str, timestamp: float) -> str:
        """
        Apply hysteresis/debouncing: `candidate_state` (the raw, frame-level
        classification) only becomes the *confirmed* state once it has been
        the candidate continuously for `debounce_seconds`. This prevents
        rapid AWAKE/DROWSY flickering from momentary noise.
        """
        if candidate_state == self.confirmed_state:
            # Already stable; clear any pending opposite-state timer.
            self._pending_state = None
            self._pending_since = None
            return self.confirmed_state

        if candidate_state != self._pending_state:
            # New candidate differs from what we were previously
            # accumulating towards -> restart the debounce timer.
            self._pending_state = candidate_state
            self._pending_since = timestamp
            return self.confirmed_state

        # Same candidate as before -- check if it's held long enough.
        assert self._pending_since is not None
        if timestamp - self._pending_since >= self.debounce_seconds:
            self.confirmed_state = candidate_state
            self._pending_state = None
            self._pending_since = None

        return self.confirmed_state

    def reset(self) -> None:
        """Reset all temporal state (e.g. when face detection is lost)."""
        self.eye_closed_timer = ConditionTimer()
        self.mouth_open_timer = ConditionTimer()
        self._score_history.clear()
        self._pending_state = None
        self._pending_since = None
        # Note: confirmed_state deliberately NOT reset here -- losing the
        # face for a frame shouldn't itself declare the driver AWAKE again.
