"""
test_detector.py
==================

Standalone tests for DrowsinessDetector using simulated facial-feature
frames. No dependency on camera/ or facial_analysis/ -- feature dicts are
hand-constructed here, exactly as `facial_analysis/` would produce them.

Run with:

    python -m unittest drowsiness_detection.test_detector -v

or, from inside the drowsiness_detection/ folder:

    python -m unittest test_detector -v

Timestamps are injected explicitly (rather than relying on wall-clock
time) so the tests are fast and deterministic: a whole multi-second
scenario runs instantly instead of actually sleeping.
"""

import unittest

from drowsiness_detection.config import DetectorConfig
from drowsiness_detection.detector import DrowsinessDetector


def make_features(
    face_detected=True,
    avg_ear=0.30,
    mar=0.30,
    eyes_closed=False,
    mouth_open=False,
    head_tilt=0.0,
):
    """Build a facial_analysis-style feature dict for tests."""
    return {
        "face_detected": face_detected,
        "left_ear": avg_ear,
        "right_ear": avg_ear,
        "avg_ear": avg_ear,
        "mar": mar,
        "eye_openness": avg_ear,
        "eyes_closed": eyes_closed,
        "mouth_open": mouth_open,
        "head_tilt": head_tilt,
    }


def feed(detector, feature_fn, total_seconds, dt, start_t=0.0):
    """
    Feed `detector.update()` a sequence of frames spaced `dt` seconds
    apart, from start_t to start_t + total_seconds. `feature_fn(t)` must
    return a feature dict for timestamp t. Returns the LAST result.
    """
    t = start_t
    result = None
    while t <= start_t + total_seconds + 1e-9:
        result = detector.update(feature_fn(t), timestamp=t)
        t += dt
    return result


class TestDrowsinessDetectorBasics(unittest.TestCase):
    def setUp(self):
        # Fast debounce/smoothing so tests don't need many seconds of
        # simulated frames; defaults are still exercised in
        # TestDrowsinessDetectorDefaults below.
        self.config = DetectorConfig.from_dict(
            {
                "eye_closed_duration_threshold": 1.0,
                "mouth_open_duration_threshold": 1.0,
                "state_change_debounce": 0.5,
                "score_smoothing_window": 0.5,
            }
        )

    def make_detector(self):
        return DrowsinessDetector(config=self.config)

    # -- Test 1: Awake -----------------------------------------------------

    def test_awake_open_eyes_closed_mouth(self):
        detector = self.make_detector()
        result = detector.update(
            make_features(avg_ear=0.30, mar=0.30, eyes_closed=False), timestamp=0.0
        )
        self.assertEqual(result["state"], "AWAKE")
        self.assertIsNone(result["reason"])
        self.assertLess(result["drowsiness_score"], 0.5)

    # -- Test 2: Brief blink should NOT trigger drowsy ----------------------

    def test_brief_blink_stays_awake(self):
        detector = self.make_detector()

        def features(t):
            # Eyes closed only briefly (0.0s - 0.3s), well under the 1.0s
            # prolonged-closure threshold, then reopen.
            closed = t < 0.3
            return make_features(avg_ear=0.10 if closed else 0.30, eyes_closed=closed)

        result = feed(detector, features, total_seconds=1.5, dt=0.1)
        self.assertEqual(result["state"], "AWAKE")

    # -- Test 3: Prolonged eye closure -> DROWSY -----------------------------

    def test_prolonged_eye_closure_triggers_drowsy(self):
        detector = self.make_detector()

        def features(t):
            return make_features(avg_ear=0.10, eyes_closed=True)

        # Eyes closed continuously for 3s: exceeds the 1.0s closure
        # threshold AND the 0.5s debounce needed to confirm DROWSY.
        result = feed(detector, features, total_seconds=3.0, dt=0.1)
        self.assertEqual(result["state"], "DROWSY")
        self.assertEqual(result["reason"], "prolonged_eye_closure")
        self.assertGreaterEqual(result["drowsiness_score"], 0.5)

    def test_single_closed_eye_frame_does_not_trigger_drowsy(self):
        """A single closed-eye frame must never classify as DROWSY."""
        detector = self.make_detector()
        result = detector.update(make_features(avg_ear=0.10, eyes_closed=True), timestamp=0.0)
        self.assertNotEqual(result["state"], "DROWSY")

    # -- Test 4: Yawning increases score ------------------------------------

    def test_prolonged_yawning_increases_score(self):
        detector = self.make_detector()

        baseline = detector.update(
            make_features(avg_ear=0.30, mar=0.30, eyes_closed=False, mouth_open=False),
            timestamp=0.0,
        )

        def features(t):
            return make_features(avg_ear=0.30, mar=0.75, eyes_closed=False, mouth_open=True)

        # Mouth open continuously for 3s: exceeds 1.0s mouth-open
        # threshold + 0.5s debounce.
        result = feed(detector, features, total_seconds=3.0, dt=0.1, start_t=1.0)

        self.assertGreater(result["drowsiness_score"], baseline["drowsiness_score"])
        # Yawning alone should raise the score, but with default weights it
        # is a weaker signal than prolonged eye closure and need not, by
        # itself, cross the DROWSY threshold -- matches the spec's
        # "possible drowsiness / increased drowsiness score" expectation.
        self.assertIn(result["state"], ("AWAKE", "DROWSY"))

    def test_yawning_combined_with_eye_closure_is_stronger(self):
        detector = self.make_detector()

        def features(t):
            return make_features(avg_ear=0.10, mar=0.75, eyes_closed=True, mouth_open=True)

        result = feed(detector, features, total_seconds=3.0, dt=0.1)
        self.assertEqual(result["state"], "DROWSY")
        self.assertEqual(result["reason"], "combined_indicators")

    # -- Test 5: No face detected -> UNKNOWN --------------------------------

    def test_no_face_detected_is_unknown(self):
        detector = self.make_detector()
        result = detector.update(make_features(face_detected=False), timestamp=0.0)
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(result["reason"], "face_not_detected")
        self.assertEqual(result["drowsiness_score"], 0.0)
        self.assertEqual(result["confidence"], 0.0)

    # -- Temporal behaviour: no flapping between states ----------------------

    def test_no_rapid_flickering_between_states(self):
        """
        Alternate eyes-closed/open every 0.1s (never sustained long enough
        to be a real prolonged closure). The confirmed state must never
        flicker to DROWSY, since no single closure ever reaches the
        duration threshold.
        """
        detector = self.make_detector()
        states = []
        t = 0.0
        for i in range(30):
            closed = (i % 2 == 0)
            r = detector.update(
                make_features(avg_ear=0.10 if closed else 0.30, eyes_closed=closed),
                timestamp=t,
            )
            states.append(r["state"])
            t += 0.1

        self.assertTrue(all(s == "AWAKE" for s in states))

    # -- avg_ear derivation from left/right when missing ---------------------

    def test_avg_ear_derived_from_left_right_when_missing(self):
        detector = self.make_detector()
        features = {
            "face_detected": True,
            "left_ear": 0.08,
            "right_ear": 0.08,
            # avg_ear intentionally omitted
            "mar": 0.2,
            "head_tilt": 0.0,
        }
        # Below ear_threshold (0.21 default) via derived avg -> should be
        # treated as eyes closed on this frame.
        result = detector.update(features, timestamp=0.0)
        self.assertIn(result["state"], ("AWAKE", "DROWSY"))  # single frame: not yet drowsy
        self.assertNotEqual(result["state"], "UNKNOWN")


class TestDrowsinessDetectorDefaults(unittest.TestCase):
    """Sanity check using the real, un-shortened default thresholds."""

    def test_defaults_construct_and_run(self):
        detector = DrowsinessDetector()  # default DetectorConfig
        result = detector.update(make_features(), timestamp=0.0)
        self.assertIn(result["state"], DrowsinessDetector.VALID_STATES)

    def test_defaults_prolonged_closure_eventually_drowsy(self):
        detector = DrowsinessDetector()

        def features(t):
            return make_features(avg_ear=0.10, eyes_closed=True)

        # Default eye_closed_duration_threshold=1.5s + debounce=1.0s;
        # run well past that (5s) using default full-size smoothing window.
        result = feed(detector, features, total_seconds=5.0, dt=0.1)
        self.assertEqual(result["state"], "DROWSY")


if __name__ == "__main__":
    unittest.main()
