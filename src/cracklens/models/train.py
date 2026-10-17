"""Train and evaluate the CPU-friendly CrackLens segmenter."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from cracklens.data.prepare import prepare_dataset


def read_gray(path: str | Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L"), dtype=np.uint8)

def iter_pairs(root: Path, split: str):
    image_dir, mask_dir = root / "images" / split, root / "masks" / split
    for image_path in sorted(image_dir.glob("*.png")):
        mask_path = mask_dir / image_path.name
        if mask_path.exists():
            yield image_path, mask_path

def _scores(pred: np.ndarray, truth: np.ndarray) -> dict:
    pred, truth = pred.astype(bool), truth.astype(bool)
    tp = int(np.count_nonzero(pred & truth))
    fp = int(np.count_nonzero(pred & ~truth))
    fn = int(np.count_nonzero(~pred & truth))
    union = int(np.count_nonzero(pred | truth))
    iou = float(tp / union) if union else 1.0
    precision = float(tp / (tp + fp)) if tp + fp else 1.0
    recall = float(tp / (tp + fn)) if tp + fn else 1.0
    f1 = float(2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {"iou": iou, "precision": precision, "recall": recall, "f1": f1}

def _postprocess(mask: np.ndarray, min_component_area: int = 3) -> np.ndarray:
    cleaned = ndimage.binary_closing(mask, structure=np.ones((3, 3), dtype=bool), iterations=1)
    labels, count = ndimage.label(cleaned, structure=np.ones((3, 3), dtype=np.uint8))
    output = np.zeros_like(cleaned, dtype=bool)
    for label in range(1, count + 1):
        component = labels == label
        if int(component.sum()) >= min_component_area:
            output |= component
    return output

def predict_classical(image: np.ndarray, model: dict) -> np.ndarray:
    arr = np.asarray(image)
    gray = arr.mean(axis=2) if arr.ndim == 3 else arr
    threshold = float(model["threshold"])
    return _postprocess(gray <= threshold, int(model.get("min_component_area", 3)))

def _evaluate(root: Path, split: str, model: dict) -> dict:
    scores = []
    for image_path, mask_path in iter_pairs(root, split):
        pred = predict_classical(read_gray(image_path), model)
        truth = read_gray(mask_path) > 0
        scores.append(_scores(pred, truth))
    if not scores:
        return {"images": 0, "iou": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "mask_mAP50_95": 0.0}
    mean = {key: float(np.mean([item[key] for item in scores])) for key in scores[0]}
    mean["images"] = len(scores)
    # A threshold model has no confidence-ranked detections, so mAP is not defined.
    mean["mask_mAP50_95"] = None
    mean["mask_mAP_note"] = "not available for the classical threshold baseline"
    return mean

def train_classical(dataset_root: str | Path = "data/processed", output_dir: str | Path = "models") -> dict:
    root, out = Path(dataset_root), Path(output_dir)
    train_pairs = list(iter_pairs(root, "train"))
    if not train_pairs:
        raise FileNotFoundError(f"no paired training images under {root}")
    # Dark cracks occupy a small fraction of pixels, so image percentiles alone can skip the useful threshold range.
    candidates = list(range(30, 181, 5))
    best = None
    for threshold in candidates:
        model = {"kind": "classical_threshold", "threshold": threshold, "min_component_area": 3}
        train_scores = [_scores(predict_classical(read_gray(image_path), model), read_gray(mask_path) > 0) for image_path, mask_path in train_pairs]
        score = float(np.mean([item["iou"] for item in train_scores]))
        if best is None or score > best[0]:
            best = (score, model)
    assert best is not None
    model = best[1]
    out.mkdir(parents=True, exist_ok=True)
    model["dataset_root"] = str(root)
    model["training_mode"] = "offline_classical_baseline"
    model_path = out / "cracklens_classical.json"
    model_path.write_text(json.dumps(model, indent=2), encoding="utf-8")
    metrics = {"model": model, "train": _evaluate(root, "train", model), "val": _evaluate(root, "val", model), "test": _evaluate(root, "test", model)}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return {"model_path": str(model_path), "metrics_path": str(out / "metrics.json"), **metrics}

def train_segmentation(dataset_root: str | Path = "data/processed", output_dir: str | Path = "models", epochs: int = 1, imgsz: int = 320, device: str = "auto") -> dict:
    """Train a reproducible baseline; optionally reserve the hook for Ultralytics.

    The repository defaults to the classical baseline because it runs without a GPU or a
    large model download. A future Ultralytics run can consume the same paired dataset after
    converting masks to YOLO polygon labels.
    """
    root = Path(dataset_root)
    if not (root / "metadata.json").exists():
        prepare_dataset(root, count=24, seed=42, allow_network=False)
    if os.environ.get("CRACKLENS_USE_ULTRALYTICS", "0").lower() in {"1", "true", "yes"}:
        from .ultralytics_adapter import train_ultralytics
        return train_ultralytics(root, output_dir, epochs=epochs, imgsz=imgsz, device=device)
    result = train_classical(root, output_dir)
    result["epochs_requested"] = epochs
    result["imgsz_requested"] = imgsz
    result["device_requested"] = device
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default="data/processed")
    parser.add_argument("--output-dir", default="models")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    print(json.dumps(train_segmentation(args.dataset_root, args.output_dir, args.epochs, args.imgsz, args.device), indent=2))

if __name__ == "__main__":
    main()


