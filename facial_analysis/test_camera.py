"""
test_camera.py

Standalone test/demo for the facial_analysis module.

This script is for INDEPENDENT development and testing only. It opens the
webcam directly, which the real pipeline will NOT do — in production,
frames are handed to FacialFeatureExtractor by the camera/ module. This
file exists purely so a developer can verify the module works in
isolation before it is wired into the rest of the system.

Run with:
    python -m facial_analysis.test_camera

Controls:
    q  - quit
    l  - toggle drawing of face landmarks on the preview window

While running, try:
    - keeping eyes open, then closing them  -> avg_ear should drop,
      eyes_closed should flip to True
    - closing your mouth, then opening it   -> mar should rise,
      mouth_open should flip to True
    - tilting your head left/right          -> head_tilt should change sign/magnitude
"""

import argparse
import sys
import time

import cv2

from .feature_extractor import FacialFeatureExtractor


def _print_features(features, frame_count: int) -> None:
    """Print a compact, readable line of the structured feature output."""
    d = features.to_dict()
    if not d["face_detected"]:
        print(f"[frame {frame_count:05d}] face_detected=False (no face in view)")
        return

    print(
        f"[frame {frame_count:05d}] "
        f"avg_ear={d['avg_ear']:.3f} "
        f"mar={d['mar']:.3f} "
        f"eye_openness={d['eye_openness']:.3f} "
        f"eyes_closed={d['eyes_closed']} "
        f"mouth_open={d['mouth_open']} "
        f"head_tilt={d['head_tilt']:.1f}deg"
    )


def run_standalone_test(camera_index: int = 0, show_window: bool = True) -> None:
    """
    Open the default webcam, run the extractor on each frame, print the
    structured feature output, and optionally show a preview window with
    landmarks drawn on it.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"ERROR: could not open camera index {camera_index}.", file=sys.stderr)
        sys.exit(1)

    draw_landmarks = True
    frame_count = 0

    print("facial_analysis standalone test running.")
    print("Press 'q' to quit, 'l' to toggle landmark drawing.\n")

    with FacialFeatureExtractor() as extractor:
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("WARNING: failed to read frame from camera, retrying...")
                    time.sleep(0.05)
                    continue

                frame_count += 1
                features = extractor.extract(frame)
                _print_features(features, frame_count)

                if show_window:
                    display = frame.copy()
                    status = "FACE DETECTED" if features.face_detected else "NO FACE"
                    cv2.putText(
                        display, status, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 0) if features.face_detected else (0, 0, 255), 2,
                    )
                    if features.face_detected:
                        cv2.putText(
                            display,
                            f"EAR: {features.avg_ear:.2f}  MAR: {features.mar:.2f}",
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2,
                        )
                    cv2.imshow("facial_analysis standalone test", display)

                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                    if key == ord("l"):
                        draw_landmarks = not draw_landmarks
        finally:
            cap.release()
            if show_window:
                cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone test for facial_analysis module.")
    parser.add_argument("--camera-index", type=int, default=0, help="Webcam index (default: 0)")
    parser.add_argument("--no-window", action="store_true", help="Disable preview window (headless)")
    args = parser.parse_args()

    run_standalone_test(camera_index=args.camera_index, show_window=not args.no_window)
