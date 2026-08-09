"""Read EXIF metadata without mutating the original file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image
import piexif

from core.gps_parser import GPSCoordinate, dms_to_decimal, rational_to_float


@dataclass
class PhotoMetadata:
    """Metadata needed for stamping plus raw EXIF bytes for diagnostics."""

    path: Path
    gps: GPSCoordinate | None
    datetime_original: str = ""
    camera_make: str = ""
    camera_model: str = ""
    lens: str = ""
    exposure: str = ""
    iso: str = ""
    orientation: int | None = None
    raw_exif: dict[str, Any] = field(default_factory=dict)
    icc_profile: bytes | None = None


class ExifReader:
    """Read JPEG EXIF fields through Pillow and piexif."""

    def read(self, path: Path) -> PhotoMetadata:
        """Read metadata from an image path."""
        with Image.open(path) as image:
            exif_bytes = image.info.get("exif", b"")
            icc_profile = image.info.get("icc_profile")
        exif = piexif.load(exif_bytes) if exif_bytes else {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        gps = self._read_gps(exif.get("GPS", {}))
        zeroth = exif.get("0th", {})
        exif_ifd = exif.get("Exif", {})
        return PhotoMetadata(
            path=path,
            gps=gps,
            datetime_original=self._decode(exif_ifd.get(piexif.ExifIFD.DateTimeOriginal, b"")),
            camera_make=self._decode(zeroth.get(piexif.ImageIFD.Make, b"")),
            camera_model=self._decode(zeroth.get(piexif.ImageIFD.Model, b"")),
            lens=self._decode(exif_ifd.get(getattr(piexif.ExifIFD, "LensModel", 42036), b"")),
            exposure=str(exif_ifd.get(piexif.ExifIFD.ExposureTime, "")),
            iso=str(exif_ifd.get(piexif.ExifIFD.ISOSpeedRatings, "")),
            orientation=zeroth.get(piexif.ImageIFD.Orientation),
            raw_exif=exif,
            icc_profile=icc_profile,
        )

    def _read_gps(self, gps_ifd: dict[int, Any]) -> GPSCoordinate | None:
        lat = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
        lat_ref = self._decode(gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef, b""))
        lon = gps_ifd.get(piexif.GPSIFD.GPSLongitude)
        lon_ref = self._decode(gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef, b""))
        if not lat or not lon or not lat_ref or not lon_ref:
            return None
        altitude = gps_ifd.get(piexif.GPSIFD.GPSAltitude)
        altitude_ref = gps_ifd.get(piexif.GPSIFD.GPSAltitudeRef, 0)
        altitude_m = rational_to_float(altitude) if altitude else None
        if altitude_m is not None and altitude_ref == 1:
            altitude_m *= -1
        return GPSCoordinate(
            latitude=dms_to_decimal(lat, lat_ref),
            longitude=dms_to_decimal(lon, lon_ref),
            altitude_m=altitude_m,
        )

    def _decode(self, value: object) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore").strip("\x00 ")
        return str(value).strip() if value is not None else ""
