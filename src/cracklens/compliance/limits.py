"""Configurable crack-width screening limits.

The ACI 224R defaults below reproduce Table 4.1 in ACI 224R-01, the commonly reproduced
environmental guidance values:
0.41 mm for dry air/protective membranes, 0.30 mm for humidity/wet air, 0.18 mm for
deicing chemicals, 0.15 mm for seawater/wetting-drying, and 0.10 mm for water-retaining
structures. The Mabhas 9 value is exposed as a configurable 0.30 mm screening default;
confirm the adopted Iranian code edition and exposure class before design use. The app's
CAUTION band begins at 80% of the selected limit by configurable screening convention; that
intermediate category is a UI triage choice, not an ACI or Mabhas 9 requirement.
"""
from __future__ import annotations
from dataclasses import dataclass

ACI_224R_LIMITS_MM = {
    "dry_air": 0.41,
    "humidity": 0.30,
    "deicing": 0.18,
    "seawater_wetting_drying": 0.15,
    "water_retaining": 0.10,
}
MABHAS9_DEFAULT_LIMIT_MM = 0.30

@dataclass(frozen=True)
class CodeLimit:
    code: str
    exposure: str
    limit_mm: float
    source: str

def limits_for(code: str = "ACI224R", exposure: str = "humidity", mabhas9_limit_mm: float = MABHAS9_DEFAULT_LIMIT_MM) -> CodeLimit:
    """Return the configured limit for a code and exposure label."""
    normalized = code.strip().upper().replace(" ", "")
    if normalized in {"ACI224R", "ACI224-R"}:
        key = exposure.strip().lower()
        if key not in ACI_224R_LIMITS_MM:
            raise ValueError(f"unknown ACI 224R exposure {exposure!r}; choose {sorted(ACI_224R_LIMITS_MM)}")
        return CodeLimit("ACI224R", key, ACI_224R_LIMITS_MM[key], "ACI 224R environmental crack-width guidance")
    if normalized in {"MABHAS9", "MABHAS09", "IRNBC9"}:
        if mabhas9_limit_mm <= 0:
            raise ValueError("mabhas9_limit_mm must be positive")
        return CodeLimit("Mabhas9", exposure, float(mabhas9_limit_mm), "Iranian National Building Code Part 9 screening default")
    raise ValueError(f"unsupported code {code!r}")

def assess_crack_width(width_mm: float, *, code: str = "ACI224R", exposure: str = "humidity", caution_ratio: float = 0.80, mabhas9_limit_mm: float = MABHAS9_DEFAULT_LIMIT_MM) -> dict:
    """Return PASS, CAUTION, or FAIL for a measured crack width."""
    if width_mm < 0:
        raise ValueError("width_mm must be non-negative")
    if not 0 < caution_ratio < 1:
        raise ValueError("caution_ratio must be between 0 and 1")
    limit = limits_for(code, exposure, mabhas9_limit_mm)
    caution_limit = limit.limit_mm * caution_ratio
    if width_mm <= caution_limit:
        verdict = "PASS"
    elif width_mm <= limit.limit_mm:
        verdict = "CAUTION"
    else:
        verdict = "FAIL"
    return {"verdict": verdict, "width_mm": float(width_mm), "limit_mm": float(limit.limit_mm), "caution_limit_mm": float(caution_limit), "code": limit.code, "exposure": limit.exposure, "source": limit.source}
