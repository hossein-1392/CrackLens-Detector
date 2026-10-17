# Assumptions and execution notes

## Data access

The preparation script first imports a local paired image/mask layout from `data/raw/`, then
tries two public GitHub archives. It understands folders named `images`/`masks`, `train_img`/
`train_lab`, and equivalent common variants. The execution environment used for the initial
build blocks outbound downloads, so the generated run uses deterministic synthetic RC-beam-like
data. That fallback is marked in `data/processed/metadata.json`; it supports software smoke
tests, not claims about field performance. Set `CRACKLENS_DATASET_URL` or place a paired
image/mask dataset under `data/raw/` before a real training run. DeepCrack states its images
and annotations are restricted to non-commercial research and educational use; follow its
source terms when using or redistributing that data.

## Pixel scale

An image-level reference is required to report millimetres. The demo accepts `scale_mm` and
`scale_pixels`; when no marker is supplied it uses the image width as `scale_pixels` and
100 mm as `scale_mm`. This default is a screening assumption and must be replaced by a
calibrated ruler or marker for engineering use.

## Code limits

The compliance module exposes ACI 224R environmental screening limits and a configurable
Mabhas 9 screening default. Code editions and exposure classes vary, so the values are
reported with their source labels and are not presented as a design approval.

## Model path

The default model is an auditable classical dark-crack segmenter. If Ultralytics is installed
and `CRACKLENS_USE_ULTRALYTICS=1` is set, the training module can use a YOLO segmentation
adapter after labels are prepared. The fallback keeps the repository runnable on CPU-only
machines and makes all metrics reproducible.
