"""Crack orientation and flexural/shear screening."""
from __future__ import annotations
import numpy as np

def principal_angle_from_vertical(points_yx: np.ndarray) -> float:
    """Return the principal-axis angle from vertical in degrees, in [0, 90]."""
    points = np.asarray(points_yx, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 2:
        return 0.0
    centered = points - np.mean(points, axis=0, keepdims=True)
    covariance = np.cov(centered, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    vector = eigenvectors[:, int(np.argmax(eigenvalues))]
    dy, dx = float(vector[0]), float(vector[1])
    angle = np.degrees(np.arctan2(abs(dx), abs(dy)))
    return float(np.clip(angle, 0.0, 90.0))

def classify_orientation(angle_deg_from_vertical: float, flexural_limit_deg: float = 30.0) -> str:
    """Classify near-vertical cracks as flexural and diagonal/horizontal cracks as shear."""
    if not 0 <= angle_deg_from_vertical <= 90:
        raise ValueError("angle_deg_from_vertical must be between 0 and 90")
    return "flexural" if angle_deg_from_vertical <= flexural_limit_deg else "shear"
