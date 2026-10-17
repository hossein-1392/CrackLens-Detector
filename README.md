# CrackLens

CrackLens is an RC beam crack inspection prototype for the cross-course project in
Applications of AI in Civil Engineering and Reinforced Concrete 1. It segments dark crack
regions, measures crack length and width, classifies flexural versus shear orientation, and
screens widths against configurable ACI 224R and Iranian National Building Code (Mabhas 9)
serviceability limits.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m cracklens prepare --count 24
python -m cracklens train --epochs 1
python -m cracklens analyze --image data/processed/images/test/sample_001.png --output artifacts/sample.json
python -m cracklens demo
```

The download step is idempotent. It imports paired masks from local data or a supported
public archive, then falls back to a deterministic synthetic dataset when outbound access is
unavailable; see
[`ASSUMPTIONS.md`](ASSUMPTIONS.md). For a real dataset, place paired image and mask files in
`data/raw/` or set `CRACKLENS_DATASET_URL` before running `prepare`.
`train` uses an auditable CPU baseline by default. Its IoU is measured directly; mask mAP is
reported as unavailable for this non-confidence-ranked threshold model. To run the optional
Ultralytics YOLO segmentation adapter on a machine with the extra installed, set
`$env:CRACKLENS_USE_ULTRALYTICS = "1"` before `python -m cracklens train`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/cracklens/data` | Dataset download, validation, and deterministic fallback generation |
| `src/cracklens/models` | Classical baseline and optional Ultralytics adapter |
| `src/cracklens/quantification` | Skeleton length, width profiles, and scale conversion |
| `src/cracklens/classify` | Principal-axis orientation and crack type |
| `src/cracklens/compliance` | ACI 224R / Mabhas 9 screening verdicts |
| `src/cracklens/app.py` | Gradio demo |
| `notebooks/report.ipynb` | Executed reproducible report |
| `tests/` | Unit tests for geometry, classification, and compliance |

## Engineering interpretation

The code reports image-derived screening measurements. It does not replace a site inspection,
a calibrated crack gauge, structural analysis, or the governing code edition used by a
licensed engineer. Update the thresholds and pixel scale in `configs/default.yaml` for the
project's adopted exposure and code edition.

## Validation

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

When the optional development dependencies are installed, `python -m pytest` runs the same
tests. The report notebook is generated and executed by:

```powershell
python -m cracklens report
```
