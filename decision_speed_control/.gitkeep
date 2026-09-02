"""
vehicle_controller.py

DECISION + SPEED CONTROL ALGORITHM
-----------------------------------
This module owns exactly one job: turn a drowsiness score (0.0-1.0) coming
from the AI/vision module into a safe, gradually-changing motor PWM command
that the Arduino/integration layer can act on.

It does NOT touch OpenCV, MediaPipe, or pyserial. That separation is
intentional (see README.md, section "Architecture") so this file can be
unit-tested on its own and swapped/reused regardless of how the AI module
or the Arduino link are implemented.

Pipeline implemented here:

    raw AI score
        -> clamp + filter (moving average)
        -> threshold decision  -> DrowsinessState
        -> target PWM lookup
        -> gradual PWM step toward target
        -> result dict / compact command string
"""

from collections import deque
from enum import Enum


class DrowsinessState(Enum):
    """Discrete driver states. Also doubles as the recommended vehicle
    action, since for this project each state maps 1:1 to one action."""
    NORMAL = "NORMAL"
    MILD_DROWSY = "SLOW_DOWN"
    SEVERE_DROWSY = "STRONG_SLOW_DOWN"
    CRITICAL = "STOP"


class ScoreFilter:
    """Simple moving-average filter to stop frame-to-frame noise in the
    AI score from causing the controller to flicker between states.

    Window size is configurable; this is intentionally a plain average,
    not a Kalman filter or ML model -- that would be overengineering for
    a B.Tech prototype and adds nothing the average doesn't already fix.
    """

    def __init__(self, window_size: int = 5):
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        self._values = deque(maxlen=window_size)

    def update(self, score: float) -> float:
        self._values.append(score)
        return sum(self._values) / len(self._values)

    def reset(self):
        self._values.clear()


class VehicleController:
    """
    Main integration point.

    Usage (this is the one call your AI teammate needs):

        controller = VehicleController()
        result = controller.process(drowsiness_score)

    `result` is a dict:
        {
            "score":        float,  # filtered score, 3 decimals
            "raw_score":    float,  # score actually used before filtering
            "state":        str,    # e.g. "SEVERE_DROWSY"
            "action":       str,    # e.g. "STRONG_SLOW_DOWN"
            "target_pwm":   int,    # where the motor command is heading
            "pwm":          int,    # motor command to send THIS cycle
            "command":      str,    # compact serial string, e.g. "STRONG_SLOW_DOWN,150"
            "valid_input":  bool,   # False if the raw input had to be corrected
        }
    """

    # --- Configurable PWM levels (Arduino analogWrite range: 0-255) ---
    PWM_NORMAL = 200
    PWM_MILD = 150
    PWM_SEVERE = 100
    PWM_CRITICAL = 0

    # --- Configurable, non-scientific, tune experimentally ---
    THRESHOLD_MILD = 0.40
    THRESHOLD_SEVERE = 0.70
    THRESHOLD_CRITICAL = 0.90

    # --- How much the PWM is allowed to change per process() call ---
    PWM_STEP = 10

    # --- How many recent scores to average ---
    FILTER_WINDOW = 5

    _PWM_BY_STATE = None  # built in __init__ from the class constants above

    def __init__(self):
        self._filter = ScoreFilter(window_size=self.FILTER_WINDOW)
        self.current_pwm = self.PWM_NORMAL

        self._pwm_by_state = {
            DrowsinessState.NORMAL: self.PWM_NORMAL,
            DrowsinessState.MILD_DROWSY: self.PWM_MILD,
            DrowsinessState.SEVERE_DROWSY: self.PWM_SEVERE,
            DrowsinessState.CRITICAL: self.PWM_CRITICAL,
        }

    # ------------------------------------------------------------------
    # Input sanitation / fail-safe
    # ------------------------------------------------------------------
    def _sanitize(self, raw_score):
        """
        Never let a bad AI value crash the controller.

        Returns (score_in_range, was_valid).
        - Non-numeric / NaN input -> treated as invalid, fails safe to 1.0
          (i.e. worst case = CRITICAL/STOP is requested) rather than silently
          assuming the driver is fine.
        - Out-of-range numeric input (e.g. -0.5, 1.5) is clamped into
          [0.0, 1.0] and flagged invalid so the caller can log it.
        """
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            return 1.0, False

        if score != score:  # NaN check without importing math
            return 1.0, False

        if score < 0.0 or score > 1.0:
            return max(0.0, min(1.0, score)), False

        return score, True

    # ------------------------------------------------------------------
    # Decision logic
    # ------------------------------------------------------------------
    def _decide_state(self, filtered_score: float) -> DrowsinessState:
        if filtered_score < self.THRESHOLD_MILD:
            return DrowsinessState.NORMAL
        if filtered_score < self.THRESHOLD_SEVERE:
            return DrowsinessState.MILD_DROWSY
        if filtered_score < self.THRESHOLD_CRITICAL:
            return DrowsinessState.SEVERE_DROWSY
        return DrowsinessState.CRITICAL

    # ------------------------------------------------------------------
    # Gradual PWM control
    # ------------------------------------------------------------------
    def _step_toward(self, target_pwm: int) -> int:
        if self.current_pwm < target_pwm:
            self.current_pwm = min(self.current_pwm + self.PWM_STEP, target_pwm)
        elif self.current_pwm > target_pwm:
            self.current_pwm = max(self.current_pwm - self.PWM_STEP, target_pwm)
        return self.current_pwm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process(self, drowsiness_score) -> dict:
        clean_score, was_valid = self._sanitize(drowsiness_score)
        filtered_score = self._filter.update(clean_score)

        state = self._decide_state(filtered_score)
        target_pwm = self._pwm_by_state[state]
        pwm = self._step_toward(target_pwm)

        return {
            "score": round(filtered_score, 3),
            "raw_score": clean_score,
            "state": state.name,
            "action": state.value,
            "target_pwm": target_pwm,
            "pwm": pwm,
            "command": f"{state.value},{pwm}",
            "valid_input": was_valid,
        }

    def safe_stop_command(self) -> dict:
        """Fail-safe the integration layer can call directly if the AI
        feed or serial link drops out entirely (no data at all, not just
        a bad value). Does not depend on any prior score."""
        self.current_pwm = self._step_toward(self.PWM_CRITICAL)
        return {
            "score": None,
            "raw_score": None,
            "state": DrowsinessState.CRITICAL.name,
            "action": DrowsinessState.CRITICAL.value,
            "target_pwm": self.PWM_CRITICAL,
            "pwm": self.current_pwm,
            "command": f"{DrowsinessState.CRITICAL.value},{self.current_pwm}",
            "valid_input": False,
        }
