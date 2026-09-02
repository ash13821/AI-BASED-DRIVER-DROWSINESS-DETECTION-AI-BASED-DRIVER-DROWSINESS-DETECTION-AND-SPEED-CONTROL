"""
drowsiness_detection
=====================

Module 3 of the "AI-Based Driver Drowsiness Prevention and Speed Control
System" college project.

This package converts per-frame facial features (produced by the
`facial_analysis` module) into a driver state (AWAKE / DROWSY / UNKNOWN)
using temporal (multi-frame) analysis. It performs no camera access and
no vehicle control -- see README.md for the full responsibility boundary.

Typical usage
-------------
    from drowsiness_detection.detector import DrowsinessDetector

    detector = DrowsinessDetector()
    result = detector.update(features)
    print(result["state"])
"""

from .detector import DrowsinessDetector
from .config import DetectorConfig
from .thresholds import Thresholds

__all__ = ["DrowsinessDetector", "DetectorConfig", "Thresholds"]

__version__ = "0.1.0"
