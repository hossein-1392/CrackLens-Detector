"""Dataset preparation with public-download attempts and deterministic fallback data."""
from __future__ import annotations
import argparse
import json
import os
import shutil
from dataclasses import asdict, dataclass
from io import BytesIO
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PUBLIC_DATASET_URLS = (
    "https://github.com/yhlleo/DeepCrack/archive/refs/heads/master.zip",
    "https://github.com/cuilimeng/CrackForest-dataset/archive/refs/heads/master.zip",
)

@dataclass(frozen=True)
class DatasetSummary:
    root: str
    source: str
    seed: int
    count: int
    train: int
    val: int
    test: int
    image_size: tuple[int, int]
    download_errors: tuple[str, ...] = ()

def _clean_tree(root: Path) -> None:
    for split in ("train", "val", "test"):
        for kind in ("images", "masks"):
            folder = root / kind / split
            folder.mkdir(parents=True, exist_ok=True)
            for item in folder.glob("*"):
                if item.is_file():
                    item.unlink()

def _draw_crack(draw: ImageDraw.ImageDraw, mask_draw: ImageDraw.ImageDraw, rng: np.random.Generator, width: int, height: int, diagonal: bool) -> None:
    if diagonal:
        x0 = int(rng.integers(width // 8, width * 2 // 3))
        y0 = int(rng.integers(height // 8, height // 2))
        x1 = int(np.clip(x0 + rng.integers(width // 8, width // 2), 0, width - 1))
        y1 = int(np.clip(y0 + rng.integers(height // 5, height * 2 // 5), 0, height - 1))
    else:
        x0 = int(rng.integers(width // 5, width * 4 // 5))
        y0 = int(rng.integers(height // 8, height // 2))
        x1 = int(np.clip(x0 + rng.integers(-width // 12, width // 12 + 1), 0, width - 1))
        y1 = int(rng.integers(height // 2, height * 7 // 8))
    points = [(x0, y0), (int((x0 + x1) / 2 + rng.integers(-8, 9)), int((y0 + y1) / 2)), (x1, y1)]
    stroke = int(rng.integers(1, 4))
    draw.line(points, fill=(42, 39, 35), width=stroke, joint="curve")
    mask_draw.line(points, fill=255, width=stroke, joint="curve")

def _synthetic_pair(rng: np.random.Generator, size: tuple[int, int]) -> tuple[Image.Image, Image.Image]:
    width, height = size
    base = np.clip(rng.normal(190, 13, (height, width, 3)), 80, 235).astype(np.uint8)
    # Concrete-like mottling and a subtle beam boundary.
    for _ in range(80):
        x, y = int(rng.integers(0, width)), int(rng.integers(0, height))
        radius = int(rng.integers(1, 5))
        value = int(rng.integers(120, 220))
        base[max(0, y-radius):min(height, y+radius), max(0, x-radius):min(width, x+radius)] = value
    image = Image.fromarray(base, mode="RGB").filter(ImageFilter.GaussianBlur(radius=0.5))
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(image)
    mask_draw = ImageDraw.Draw(mask)
    count = int(rng.integers(1, 4))
    for index in range(count):
        _draw_crack(draw, mask_draw, rng, width, height, diagonal=(index % 2 == 1))
    return image, mask

def generate_synthetic_dataset(root: str | Path = "data/processed", count: int = 24, seed: int = 42, image_size: tuple[int, int] = (320, 240)) -> DatasetSummary:
    """Generate paired images and masks for a deterministic smoke-test dataset."""
    if count < 6:
        raise ValueError("count must be at least 6 so train/val/test each contain samples")
    root_path = Path(root)
    _clean_tree(root_path)
    rng = np.random.default_rng(seed)
    indices = np.arange(count)
    rng.shuffle(indices)
    train_cut = max(1, int(round(count * 0.70)))
    val_cut = max(train_cut + 1, int(round(count * 0.85)))
    split_for = {int(idx): ("train" if pos < train_cut else "val" if pos < val_cut else "test") for pos, idx in enumerate(indices)}
    counts = {"train": 0, "val": 0, "test": 0}
    for idx in range(count):
        split = split_for[idx]
        image, mask = _synthetic_pair(rng, image_size)
        stem = f"sample_{idx:03d}"
        image.save(root_path / "images" / split / f"{stem}.png")
        mask.save(root_path / "masks" / split / f"{stem}.png")
        counts[split] += 1
    summary = DatasetSummary(str(root_path), "synthetic_fallback", seed, count, counts["train"], counts["val"], counts["test"], image_size)
    (root_path / "metadata.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    return summary

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
IMAGE_DIR_NAMES = {"image", "images", "img", "imgs", "trainimg", "testimg"}
MASK_DIR_NAMES = {"mask", "masks", "label", "labels", "lab", "gt", "groundtruth", "segmentation", "segment"}

def _directory_role(path: Path) -> str | None:
    for parent in path.parents:
        name = parent.name.lower().replace("_", "").replace("-", "")
        if name in IMAGE_DIR_NAMES or name.endswith("image") or name.endswith("img"):
            return "image"
        if name in MASK_DIR_NAMES or name.endswith("mask") or name.endswith("label") or name.endswith("lab"):
            return "mask"
    return None

def _normalized_stem(path: Path) -> str:
    stem = path.stem.lower()
    for suffix in ("_mask", "_label", "_gt", "_groundtruth", "_seg"):
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
    return stem

def _pair_images_and_masks(search_root: Path) -> list[tuple[Path, Path]]:
    if not search_root.exists():
        return []
    images: list[Path] = []
    masks: list[Path] = []
    for path in search_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        role = _directory_role(path)
        if role == "image":
            images.append(path)
        elif role == "mask":
            masks.append(path)
    masks_by_stem: dict[str, list[Path]] = {}
    for path in masks:
        masks_by_stem.setdefault(_normalized_stem(path), []).append(path)
    pairs: list[tuple[Path, Path]] = []
    for image_path in images:
        candidates = masks_by_stem.get(_normalized_stem(image_path), [])
        if not candidates:
            continue
        # Prefer the matching train/test annotation directory when multiple copies share a stem.
        def common_parent_score(candidate: Path) -> int:
            left, right = image_path.parent.parts, candidate.parent.parts
            score = 0
            for left_part, right_part in zip(left, right):
                if left_part.lower() != right_part.lower():
                    break
                score += 1
            return score
        mask_path = max(candidates, key=common_parent_score)
        pairs.append((image_path, mask_path))
    unique: dict[str, tuple[Path, Path]] = {}
    for image_path, mask_path in pairs:
        key = str(image_path.resolve()).lower()
        unique[key] = (image_path, mask_path)
    return sorted(unique.values(), key=lambda pair: str(pair[0]).lower())

def _split_pairs(pairs: list[tuple[Path, Path]], seed: int) -> dict[str, list[tuple[Path, Path]]]:
    if len(pairs) < 3:
        return {}
    indices = np.arange(len(pairs))
    np.random.default_rng(seed).shuffle(indices)
    train_count = min(max(1, int(round(len(pairs) * 0.70))), len(pairs) - 2)
    val_count = min(max(1, int(round(len(pairs) * 0.15))), len(pairs) - train_count - 1)
    return {
        "train": [pairs[int(i)] for i in indices[:train_count]],
        "val": [pairs[int(i)] for i in indices[train_count:train_count + val_count]],
        "test": [pairs[int(i)] for i in indices[train_count + val_count:]],
    }

def import_paired_dataset(search_root: str | Path, output_root: str | Path = "data/processed", seed: int = 42, source: str = "local_paired_dataset") -> DatasetSummary | None:
    """Import matching image/mask files from common image and label directory layouts."""
    pairs = _pair_images_and_masks(Path(search_root))
    splits = _split_pairs(pairs, seed)
    if not splits:
        return None
    output = Path(output_root)
    _clean_tree(output)
    counts = {split: 0 for split in ("train", "val", "test")}
    first_size: tuple[int, int] | None = None
    for split, split_pairs in splits.items():
        for index, (image_path, mask_path) in enumerate(split_pairs):
            with Image.open(image_path) as source_image:
                image = source_image.convert("RGB")
            with Image.open(mask_path) as source_mask:
                mask = source_mask.convert("L")
            if image.size != mask.size:
                raise ValueError(f"image/mask size mismatch for {image_path.name}: {image.size} vs {mask.size}")
            if first_size is None:
                first_size = image.size
            stem = f"sample_{counts[split]:04d}_{image_path.stem}"
            image.save(output / "images" / split / f"{stem}.png")
            mask.save(output / "masks" / split / f"{stem}.png")
            counts[split] += 1
    count = sum(counts.values())
    summary = DatasetSummary(str(output), source, seed, count, counts["train"], counts["val"], counts["test"], first_size or (0, 0))
    (output / "metadata.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    return summary

def _try_download(url: str, raw_root: Path) -> Path:
    raw_root.mkdir(parents=True, exist_ok=True)
    digest = sha256(url.encode("utf-8")).hexdigest()[:12]
    archive = raw_root / f"dataset_{digest}.zip"
    extract_root = raw_root / f"archive_{digest}"
    if not archive.exists():
        request = Request(url, headers={"User-Agent": "CrackLens/0.1"})
        with urlopen(request, timeout=15) as response:
            payload = response.read()
        archive.write_bytes(payload)
    else:
        payload = archive.read_bytes()
    extract_root.mkdir(parents=True, exist_ok=True)
    with ZipFile(BytesIO(payload)) as zipped:
        resolved_root = extract_root.resolve()
        for member in zipped.infolist():
            destination = (extract_root / member.filename).resolve()
            if not destination.is_relative_to(resolved_root):
                raise ValueError(f"archive contains an unsafe path: {member.filename}")
        zipped.extractall(extract_root)
    return extract_root

def prepare_dataset(root: str | Path = "data/processed", count: int = 24, seed: int = 42, allow_network: bool = True) -> DatasetSummary:
    """Use local or downloaded paired labels, then fall back to deterministic synthetic data."""
    root_path = Path(root)
    raw_root = Path("data/raw")
    errors: list[str] = []

    local_summary = import_paired_dataset(raw_root, root_path, seed, source="local_paired_dataset")
    if local_summary is not None:
        return local_summary

    requested_url = os.environ.get("CRACKLENS_DATASET_URL")
    urls = (requested_url,) if requested_url else PUBLIC_DATASET_URLS
    if allow_network:
        for url in urls:
            try:
                extracted_root = _try_download(url, raw_root)
                summary = import_paired_dataset(extracted_root, root_path, seed, source=url)
                if summary is not None:
                    summary = DatasetSummary(summary.root, summary.source, summary.seed, summary.count, summary.train, summary.val, summary.test, summary.image_size, tuple(errors))
                    (root_path / "metadata.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
                    return summary
                errors.append(f"{url}: archive contained no recognized paired image/mask directories")
            except (HTTPError, URLError, OSError, TimeoutError, BadZipFile, ValueError) as exc:  # network is optional
                errors.append(f"{url}: {type(exc).__name__}: {exc}")

    summary = generate_synthetic_dataset(root_path, count=count, seed=seed)
    summary = DatasetSummary(summary.root, summary.source, summary.seed, summary.count, summary.train, summary.val, summary.test, summary.image_size, tuple(errors))
    (root_path / "metadata.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    return summary

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="data/processed")
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    summary = prepare_dataset(args.root, args.count, args.seed, allow_network=not args.offline)
    print(json.dumps(asdict(summary), indent=2))

if __name__ == "__main__":
    main()

