"""GPS coordinate conversion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable


@dataclass(frozen=True)
class GPSCoordinate:
    """Decimal GPS coordinate with optional altitude."""

    latitude: float
    longitude: float
    altitude_m: float | None = None


def rational_to_float(value: object) -> float:
    """Convert EXIF rational representations to float."""
    if isinstance(value, tuple) and len(value) == 2:
        numerator, denominator = value
        return float(Fraction(int(numerator), int(denominator) or 1))
    if isinstance(value, Fraction):
        return float(value)
    return float(value)


def dms_to_decimal(dms: Iterable[object], ref: str) -> float:
    """Convert EXIF degrees/minutes/seconds and hemisphere to decimal degrees."""
    degrees, minutes, seconds = [rational_to_float(item) for item in dms]
    decimal = degrees + minutes / 60.0 + seconds / 3600.0
    if ref.upper() in {"S", "W"}:
        decimal *= -1
    return decimal
