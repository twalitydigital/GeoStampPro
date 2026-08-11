# Third-Party Notices

Twality GMark Pro uses third-party components and services. This file is provided as
a practical notice for packaging and Microsoft Store review. Verify exact dependency
versions and license texts before final publication.

## Python Packages

The Windows app depends on packages listed in `requirements.txt`, including:

- PySide6
- Pillow
- piexif
- PyExifTool
- requests
- staticmap
- geopy
- pillow-heif

Each dependency is distributed under its own license. Review the installed package
metadata in the release environment before publishing.

## External Tools

- ExifTool is required for full JPEG metadata preservation. ExifTool is not bundled by
  this project unless explicitly added to a release package. Users can install it
  separately and make `exiftool.exe` available on PATH.

## External Services

- OpenStreetMap Nominatim may be used for reverse geocoding.
- Map imagery may be retrieved from the configured map provider.

Use of these services may be subject to their own usage policies and availability.
