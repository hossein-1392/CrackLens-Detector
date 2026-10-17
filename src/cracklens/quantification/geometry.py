"""Geometry utilities for binary crack masks.

The implementation has no hard dependency on OpenCV or scikit-image. If scikit-image is
available it is used for skeletonization; otherwise a compact Zhang-Suen implementation is
used. Width is estimated from the binary distance transform at skeleton pixels, with the
pixel-centre correction ``2*d - 1`` so a one-pixel crack measures one pixel wide.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import math
import numpy as np
from scipy import ndimage
from cracklens.classify.orientation import classify_orientation, principal_angle_from_vertical

@dataclass(frozen=True)
class CrackMeasurement:
    """Measured geometry for one connected crack component."""
    crack_id: int
    length_px: float
    length_mm: float
    max_width_px: float
    mean_width_px: float
    max_width_mm: float
    mean_width_mm: float
    angle_deg_from_vertical: float
    classification: str
    pixel_size_mm: float
    centroid_x: float
    centroid_y: float
    def to_dict(self) -> dict:
        return asdict(self)

def _as_bool_mask(mask: np.ndarray) -> np.ndarray:
    arr = np.asarray(mask)
    if arr.ndim != 2:
        raise ValueError(f"expected a 2-D mask, got shape {arr.shape}")
    return arr.astype(bool)

def _zhang_suen(mask: np.ndarray) -> np.ndarray:
    """Zhang-Suen thinning fallback for environments without scikit-image."""
    img = mask.astype(np.uint8).copy()
    if not img.any():
        return img.astype(bool)
    changed = True
    while changed:
        changed = False
        for phase in (0, 1):
            padded = np.pad(img, 1, mode="constant")
            p2, p3, p4 = padded[:-2, 1:-1], padded[:-2, 2:], padded[1:-1, 2:]
            p5, p6, p7 = padded[2:, 2:], padded[2:, 1:-1], padded[2:, :-2]
            p8, p9 = padded[1:-1, :-2], padded[:-2, :-2]
            neighbours = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            transitions = (
                ((p2 == 0) & (p3 == 1)).astype(np.uint8)
                + ((p3 == 0) & (p4 == 1)).astype(np.uint8)
                + ((p4 == 0) & (p5 == 1)).astype(np.uint8)
                + ((p5 == 0) & (p6 == 1)).astype(np.uint8)
                + ((p6 == 0) & (p7 == 1)).astype(np.uint8)
                + ((p7 == 0) & (p8 == 1)).astype(np.uint8)
                + ((p8 == 0) & (p9 == 1)).astype(np.uint8)
                + ((p9 == 0) & (p2 == 1)).astype(np.uint8)
            )
            if phase == 0:
                condition = ((img == 1) & (neighbours >= 2) & (neighbours <= 6) & (transitions == 1) & ((p2 * p4 * p6) == 0) & ((p4 * p6 * p8) == 0))
            else:
                condition = ((img == 1) & (neighbours >= 2) & (neighbours <= 6) & (transitions == 1) & ((p2 * p4 * p8) == 0) & ((p2 * p6 * p8) == 0))
            if condition.any():
                img[condition] = 0
                changed = True
    return img.astype(bool)

def skeletonize_mask(mask: np.ndarray) -> np.ndarray:
    """Return a one-pixel-wide skeleton for a binary mask."""
    binary = _as_bool_mask(mask)
    try:
        from skimage.morphology import skeletonize  # type: ignore
        return skeletonize(binary)
    except ImportError:
        return _zhang_suen(binary)

def skeleton_length_px(skeleton: np.ndarray) -> float:
    """Estimate geodesic length by summing each 8-neighbour edge once."""
    skel = _as_bool_mask(skeleton)
    if not skel.any():
        return 0.0
    length = 0.0
    for dy, dx, weight in ((0, 1, 1.0), (1, 0, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2))):
        y0, y1 = max(0, -dy), skel.shape[0] - max(0, dy)
        x0, x1 = max(0, -dx), skel.shape[1] - max(0, dx)
        source = skel[y0:y1, x0:x1]
        target = skel[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
        length += float(np.count_nonzero(source & target)) * weight
    return length

def width_profile_px(mask: np.ndarray, skeleton: np.ndarray | None = None) -> np.ndarray:
    """Estimate full crack width at skeleton points in pixels."""
    binary = _as_bool_mask(mask)
    skel = skeletonize_mask(binary) if skeleton is None else _as_bool_mask(skeleton)
    if not skel.any():
        return np.empty(0, dtype=float)
    distance = ndimage.distance_transform_edt(binary)
    values = 2.0 * distance[skel] - 1.0
    return np.maximum(values, 1.0)

def measure_crack(mask: np.ndarray, *, crack_id: int = 1, scale_mm: float = 100.0, scale_pixels: float | None = None) -> CrackMeasurement:
    """Measure one crack mask and classify its principal-axis orientation.

    ``scale_mm`` is the physical length represented by ``scale_pixels``. If no pixel
    reference is supplied, the mask width is used as a deterministic screening fallback.
    """
    binary = _as_bool_mask(mask)
    ys, xs = np.nonzero(binary)
    if len(xs) == 0:
        raise ValueError("cannot measure an empty crack mask")
    if scale_mm <= 0:
        raise ValueError("scale_mm must be positive")
    reference_pixels = float(scale_pixels if scale_pixels is not None else binary.shape[1])
    if reference_pixels <= 0:
        raise ValueError("scale_pixels must be positive")
    pixel_size_mm = float(scale_mm) / reference_pixels
    skeleton = skeletonize_mask(binary)
    length_px = skeleton_length_px(skeleton)
    # Thinning can shorten the ends of a thick component. Use the major-axis extent as
    # a conservative endpoint correction while retaining the skeleton geodesic for bends.
    points = np.column_stack((ys, xs)).astype(float)
    centered = points - np.mean(points, axis=0, keepdims=True)
    if len(points) >= 2:
        _, _, vh = np.linalg.svd(centered, full_matrices=False)
        major_extent = float(np.ptp(centered @ vh[0]))
        length_px = max(length_px, major_extent)
    widths = width_profile_px(binary, skeleton)
    if widths.size == 0:
        widths = np.array([1.0])
    angle = principal_angle_from_vertical(np.column_stack((ys, xs)))
    classification = classify_orientation(angle)
    return CrackMeasurement(crack_id=int(crack_id), length_px=float(length_px), length_mm=float(length_px * pixel_size_mm), max_width_px=float(np.max(widths)), mean_width_px=float(np.mean(widths)), max_width_mm=float(np.max(widths) * pixel_size_mm), mean_width_mm=float(np.mean(widths) * pixel_size_mm), angle_deg_from_vertical=float(angle), classification=classification, pixel_size_mm=pixel_size_mm, centroid_x=float(np.mean(xs)), centroid_y=float(np.mean(ys)))

def connected_components(mask: np.ndarray, min_area: int = 3) -> list[np.ndarray]:
    """Split a binary mask into component masks, largest first."""
    binary = _as_bool_mask(mask)
    labels, count = ndimage.label(binary, structure=np.ones((3, 3), dtype=np.uint8))
    components: list[np.ndarray] = []
    for label in range(1, count + 1):
        component = labels == label
        if int(component.sum()) >= min_area:
            components.append(component)
    components.sort(key=lambda item: int(item.sum()), reverse=True)
    return components

__all__ = ["CrackMeasurement", "connected_components", "measure_crack", "skeleton_length_px", "skeletonize_mask", "width_profile_px"]
