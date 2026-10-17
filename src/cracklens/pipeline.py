"""End-to-end crack segmentation, geometry, classification, and code screening."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from PIL import Image
from cracklens.compliance import assess_crack_width
from cracklens.models.inference import load_image, segment_image
from cracklens.quantification.geometry import connected_components, measure_crack

def _fallback_segment(image: np.ndarray) -> np.ndarray:
    gray = image.mean(axis=2)
    threshold = float(np.percentile(gray, 12))
    return gray <= threshold

def _overlay(image: np.ndarray, records: list[dict], components: list[np.ndarray]) -> Image.Image:
    base = image.astype(np.float32).copy()
    colors = {"PASS": np.array([58, 170, 112]), "CAUTION": np.array([232, 163, 58]), "FAIL": np.array([215, 70, 70])}
    for record, component in zip(records, components):
        color = colors.get(record["verdict"], np.array([65, 130, 220]))
        base[component] = 0.45 * base[component] + 0.55 * color
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), mode="RGB")

def analyze_image(image, *, model_path: str | Path = "models/cracklens_classical.json", reference_mm: float = 100.0, reference_pixels: float | None = None, code: str = "ACI224R", exposure: str = "humidity", mabhas9_limit_mm: float = 0.30, min_component_area: int = 3) -> dict:
    """Analyze an image and return an overlay, records, mask, and summary."""
    image_array = load_image(image)
    try:
        _, segmentation = segment_image(image_array, model_path)
    except FileNotFoundError:
        segmentation = _fallback_segment(image_array)
    components = connected_components(segmentation, min_area=min_component_area)
    scale_pixels = reference_pixels if reference_pixels is not None else float(image_array.shape[1])
    records: list[dict] = []
    for index, component in enumerate(components, start=1):
        measurement = measure_crack(component, crack_id=index, scale_mm=reference_mm, scale_pixels=scale_pixels)
        compliance = assess_crack_width(measurement.max_width_mm, code=code, exposure=exposure, mabhas9_limit_mm=mabhas9_limit_mm)
        row = measurement.to_dict()
        row.update({"verdict": compliance["verdict"], "limit_mm": compliance["limit_mm"], "code": compliance["code"], "exposure": compliance["exposure"]})
        records.append(row)
    overlay = _overlay(image_array, records, components)
    summary = {"component_count": len(records), "max_width_mm": max((row["max_width_mm"] for row in records), default=0.0), "failures": sum(row["verdict"] == "FAIL" for row in records), "code": code, "exposure": exposure, "reference_mm": reference_mm, "reference_pixels": scale_pixels}
    return {"overlay": overlay, "records": records, "mask": segmentation, "summary": summary}

def save_analysis(result: dict, output_path: str | Path) -> None:
    payload = {"summary": result["summary"], "records": result["records"]}
    Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
