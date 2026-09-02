"""
facial_analysis

Module 2 of the AI-Based Driver Drowsiness Prevention and Speed Control
System.

Responsibility: Video frame -> Face landmarks -> Numerical facial features.
This module does NOT decide drowsiness — see drowsiness_detection/ for that.

Public API:
    from facial_analysis.feature_extractor import FacialFeatureExtractor, FacialFeatures
"""

from .feature_extractor import FacialFeatureExtractor, FacialFeatures

__all__ = ["FacialFeatureExtractor", "FacialFeatures"]
