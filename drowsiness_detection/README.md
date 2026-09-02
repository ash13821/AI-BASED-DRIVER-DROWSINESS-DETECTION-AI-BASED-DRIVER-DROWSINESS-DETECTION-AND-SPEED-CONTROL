# drowsiness_detection

Module 3 of 6 in the **AI-Based Driver Drowsiness Prevention and Speed
Control System** college project.

```
Camera → Facial Analysis → Drowsiness Detection → Decision + Speed Control → Vehicle Simulation
                                  (this module)
```

This module turns per-frame facial features into a driver state
(`AWAKE` / `DROWSY` / `UNKNOWN`) using **temporal** analysis (durations,
smoothing, hysteresis) — never a single frame in isolation. It does not
touch the camera, does not compute facial landmarks, and does not control
the vehicle.

---

## 1. Folder structure

```
drowsiness_detection/
├── __init__.py        # exposes DrowsinessDetector, DetectorConfig, Thresholds
├── config.py           # DetectorConfig + ScoreWeights (how signals combine)
├── thresholds.py        # Thresholds (raw EAR/MAR/duration cut-offs)
├── state_tracker.py     # temporal history: durations, smoothing, debounce
├── detector.py           # DrowsinessDetector — the public interface
├── test_detector.py      # standalone unit tests (simulated inputs)
├── requirements.txt       # stdlib only — no third-party deps
└── README.md             # this file
```

## 2. Install dependencies

None. The module uses only the Python 3.12 standard library
(`dataclasses`, `collections`, `time`, `typing`, `unittest`).
`requirements.txt` documents this explicitly. If you keep it in a shared
virtualenv with the other modules, just running

```bash
pip install -r drowsiness_detection/requirements.txt
```

is a no-op but harmless.

## 3. Run the standalone tests

From the project root (the folder that *contains* `drowsiness_detection/`):

```bash
python -m unittest drowsiness_detection.test_detector -v
```

or from inside `drowsiness_detection/`:

```bash
python -m unittest test_detector -v
```

The tests build feature dicts by hand (no camera, no `facial_analysis/`
dependency) and inject explicit timestamps, so a multi-second scenario
(e.g. "eyes closed for 3 seconds") runs instantly and deterministically
instead of sleeping in real time.

## 4. Example input (from `facial_analysis/`)

```python
features = {
    "face_detected": True,
    "left_ear": 0.28,
    "right_ear": 0.30,
    "avg_ear": 0.29,
    "mar": 0.35,
    "eye_openness": 0.29,
    "eyes_closed": False,
    "mouth_open": False,
    "head_tilt": 2.4,
}
```

Only `face_detected` is required; everything else is optional and the
detector degrades gracefully if fields are missing (e.g. it derives
`avg_ear` from `left_ear`/`right_ear` if `avg_ear` is absent).

## 5. Example output

```python
from drowsiness_detection.detector import DrowsinessDetector

detector = DrowsinessDetector()
result = detector.update(features)
```

Awake:

```python
{"state": "AWAKE", "drowsiness_score": 0.10, "confidence": 0.92, "reason": None}
```

Drowsy:

```python
{"state": "DROWSY", "drowsiness_score": 0.82, "confidence": 0.88, "reason": "prolonged_eye_closure"}
```

No face detected:

```python
{"state": "UNKNOWN", "drowsiness_score": 0.0, "confidence": 0.0, "reason": "face_not_detected"}
```

`reason` is one of: `None`, `"prolonged_eye_closure"`, `"yawning"`,
`"combined_indicators"`, `"head_tilt"`, `"elevated_drowsiness_score"`,
`"face_not_detected"`.

## 6. How temporal detection works

Every call to `update()` should pass a `timestamp` (seconds — real
wall-clock time, a video frame's PTS, or a simulated clock in tests). If
omitted, `time.time()` is used.

1. **Duration tracking** (`state_tracker.ConditionTimer`) — for each
   frame, "eyes closed" and "mouth open" are booleans; the tracker
   measures how long each has been *continuously* true. A blink resets
   the timer back to 0 as soon as the eyes reopen, so it never
   accumulates into "prolonged closure."
2. **Scoring with a ramp** — once a duration crosses its threshold, its
   contribution to the raw per-frame score ramps up further the longer
   it continues (from 0.6× to 1.0× of that signal's weight as duration
   goes from 1× to 2× the threshold), rewarding sustained closure over a
   borderline one.
3. **Smoothing** (`StateTracker.push_score`) — raw per-frame scores are
   averaged over a rolling `score_smoothing_window` (default 1.0s) to
   reduce frame-to-frame noise (e.g. one bad EAR reading).
4. **Debounce/hysteresis** (`StateTracker.resolve_state`) — the smoothed
   score is compared to `drowsiness_score_threshold` to get a
   *candidate* state each frame, but the *confirmed* state (what
   `update()` returns) only changes once the candidate has been
   consistent for `state_change_debounce` seconds. This is what prevents
   `AWAKE, DROWSY, AWAKE, DROWSY, ...` flicker.

Net effect: a single closed-eye frame can never produce `DROWSY` — it
takes sustained closure (or combined signals) held long enough to get
through both the duration threshold and the debounce window.

## 7. Configurable thresholds

All in `thresholds.py` (`Thresholds` dataclass), overridable via
`DetectorConfig.from_dict({...})` or by constructing `Thresholds(...)`
directly. **None of these are medically validated** — they're
reasonable starting points for a prototype; tune per camera/lighting.

| Field | Default | Meaning |
|---|---|---|
| `ear_threshold` | 0.21 | EAR below this = eyes closed, for one frame |
| `eye_closed_duration_threshold` | 1.5s | continuous closure beyond this = "prolonged" (vs. a blink) |
| `mar_threshold` | 0.55 | MAR above this = mouth open, for one frame |
| `mouth_open_duration_threshold` | 1.2s | continuous open-mouth beyond this = "yawn" |
| `head_tilt_threshold` | 15.0° | absolute tilt beyond this contributes a weak signal |
| `drowsiness_score_threshold` | 0.5 | smoothed score at/above this = candidate DROWSY |
| `score_smoothing_window` | 1.0s | rolling window for averaging raw scores |
| `state_change_debounce` | 1.0s | how long a candidate state must hold before it's confirmed |

Signal *weights* (how much each contributes to the 0–1 score) live in
`config.py` (`ScoreWeights`): `eye_closed_instant` (0.10),
`eye_closed_prolonged` (0.55), `yawn_instant` (0.05), `yawn_prolonged`
(0.25), `head_tilt` (0.10). Prolonged closure alone can reach `DROWSY`;
yawning alone is weaker by design and combines with other signals for a
stronger, faster detection (see `test_yawning_combined_with_eye_closure_is_stronger`).

## 8. Interface for `decision_speed_control/`

```python
from drowsiness_detection.detector import DrowsinessDetector

detector = DrowsinessDetector()

# per frame, after facial_analysis produces `features`:
result = detector.update(features, timestamp=frame_timestamp)

if result["state"] == "DROWSY":
    # decision_speed_control/ decides NORMAL / SLOW_DOWN / EMERGENCY_BRAKE
    # from here — this module never calls brake()/slow_down()/set_speed().
    ...
elif result["state"] == "UNKNOWN":
    # e.g. treat as "insufficient information" — decision module's call.
    ...
```

`result` is always a dict with exactly these keys:
`state` (`"AWAKE"|"DROWSY"|"UNKNOWN"`), `drowsiness_score` (float,
0.0–1.0), `confidence` (float, 0.0–1.0), `reason` (str or `None`).

## 9. Not implemented here (by design)

- Camera capture, face detection, EAR/MAR computation → `facial_analysis/`
- `brake()`, `slow_down()`, `set_speed()`, any control decision → `decision_speed_control/`
- Vehicle physics/behaviour → `vehicle_simulation/`
- UI/dashboard → `dashboard_integration/`

An optional real-time test (camera → facial_analysis → this detector) can
be added later as a *separate* script that imports both modules; the
core `DrowsinessDetector` class itself has no camera dependency, so it
stays testable in isolation as shown in section 3.
