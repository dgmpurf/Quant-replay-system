"""Calibration placeholders."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationPlan:
    """A record of what should be calibrated after baseline replay works."""

    weights: bool = True
    thresholds: bool = True
    risk_rules: bool = True


def default_calibration_plan() -> CalibrationPlan:
    """Return the MVP calibration roadmap."""

    return CalibrationPlan()
