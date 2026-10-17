"""Optional Ultralytics YOLO segmentation adapter.

This module is intentionally optional. It is used only when the user installs Ultralytics and
sets ``CRACKLENS_USE_ULTRALYTICS=1``. The default offline baseline does not download weights.
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

def _component_polygon(component: np.ndarray) -> list[tuple[float, float]]:
    boundary = component & ~ndimage.binary_erosion(component, structure=np.ones((3, 3), dtype=bool))
    ys, xs = np.nonzero(boundary)
    if len(xs) < 3:
        ys, xs = np.nonzero(component)
    if len(xs) == 0:
        return []
    # A compact convex-ish outline keeps labels small and works without OpenCV.
    points = np.column_stack((xs, ys)).astype(float)
    center = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    order = np.argsort(angles)
    selected = points[order][::max(1, len(order) // 64)]
    return [(float(x), float(y)) for x, y in selected]

def build_yolo_dataset(dataset_root: str | Path, output_root: str | Path = "data/yolo") -> Path:
    root, out = Path(dataset_root), Path(output_root)
    for split in ("train", "val", "test"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)
        for image_path in sorted((root / "images" / split).glob("*.png")):
            mask_path = root / "masks" / split / image_path.name
            if not mask_path.exists():
                continue
            shutil.copy2(image_path, out / "images" / split / image_path.name)
            mask = np.asarray(Image.open(mask_path).convert("L")) > 0
            labels = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))[0]
            h, w = mask.shape
            rows = []
            for label in range(1, int(labels.max()) + 1):
                polygon = _component_polygon(labels == label)
                if len(polygon) < 3:
                    continue
                coords = []
                for x, y in polygon:
                    coords.extend((x / w, y / h))
                rows.append("0 " + " ".join(f"{v:.6f}" for v in coords))
            (out / "labels" / split / f"{image_path.stem}.txt").write_text("\n".join(rows), encoding="utf-8")
    yaml_text = f"path: {out.resolve().as_posix()}\ntrain: images/train\nval: images/val\ntest: images/test\nnc: 1\nnames: [crack]\n"
    (out / "data.yaml").write_text(yaml_text, encoding="utf-8")
    return out

def train_ultralytics(dataset_root: str | Path = "data/processed", output_dir: str | Path = "models", epochs: int = 20, imgsz: int = 320, device: str = "auto") -> dict:
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Ultralytics is not installed; install the optional training extra first") from exc
    data_root = build_yolo_dataset(dataset_root)
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    resolved_device = device
    if device.lower() == "auto":
        import torch
        resolved_device = 0 if torch.cuda.is_available() else "cpu"
    model = YOLO("yolov8n-seg.pt")
    model.train(data=str(data_root / "data.yaml"), epochs=epochs, imgsz=imgsz, device=resolved_device, project=str(out), name="cracklens_yolo", exist_ok=True)
    best = out / "cracklens_yolo" / "weights" / "best.pt"
    if not best.exists():
        raise FileNotFoundError(f"Ultralytics did not produce best weights at {best}")
    destination = out / "cracklens_yolo_best.pt"
    shutil.copy2(best, destination)
    validator = YOLO(str(destination))
    test_metrics = validator.val(data=str(data_root / "data.yaml"), split="test", imgsz=imgsz, device=resolved_device, verbose=False)
    metrics = {
        "model": "yolov8n-seg",
        "weights": str(destination),
        "epochs": epochs,
        "imgsz": imgsz,
        "device": str(resolved_device),
        "test_mask_mAP50": float(test_metrics.seg.map50),
        "test_mask_mAP50_95": float(test_metrics.seg.map),
    }
    (out / "ultralytics_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics
