"""Model loading and image segmentation."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .train import predict_classical

def load_model(model_path: str | Path = "models/cracklens_classical.json") -> dict:
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"model file not found: {path}; run `python -m cracklens train` first")
    return json.loads(path.read_text(encoding="utf-8"))

def load_image(image: str | Path | Image.Image | np.ndarray) -> np.ndarray:
    if isinstance(image, (str, Path)):
        return np.asarray(Image.open(image).convert("RGB"))
    if isinstance(image, Image.Image):
        return np.asarray(image.convert("RGB"))
    arr = np.asarray(image)
    if arr.ndim == 2:
        return np.repeat(arr[..., None], 3, axis=2)
    if arr.ndim != 3 or arr.shape[2] not in (3, 4):
        raise ValueError(f"expected an RGB image, got shape {arr.shape}")
    return arr[..., :3].astype(np.uint8)

def segment_image(image: str | Path | Image.Image | np.ndarray, model_path: str | Path = "models/cracklens_classical.json") -> tuple[np.ndarray, np.ndarray]:
    arr = load_image(image)
    path = Path(model_path)
    if path.suffix.lower() == ".pt":
        try:
            from ultralytics import YOLO  # type: ignore
        except ImportError as exc:
            raise RuntimeError("This model requires the optional Ultralytics training extra") from exc
        model = YOLO(str(path))
        prediction = model.predict(arr, verbose=False)
        masks = prediction[0].masks
        combined = np.zeros(arr.shape[:2], dtype=bool)
        if masks is not None:
            for raw_mask in masks.data.cpu().numpy():
                resized = Image.fromarray((raw_mask > 0.5).astype(np.uint8) * 255).resize((arr.shape[1], arr.shape[0]), Image.Resampling.NEAREST)
                combined |= np.asarray(resized) > 0
        return arr, combined
    model = load_model(path)
    if model.get("kind") != "classical_threshold":
        raise ValueError(f"unsupported model kind: {model.get('kind')}")
    return arr, predict_classical(arr, model)
