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

- ExifTool 13.59 by Phil Harvey is bundled privately for full JPEG metadata
  preservation. Architecture-specific Windows executables are kept under
  `vendor\exiftool\x64` and `vendor\exiftool\x86` with each copy's required
  `exiftool_files` folder. ExifTool is distributed under the Perl Artistic License.
  Official project site: https://exiftool.org/

## External Services

- OpenStreetMap Nominatim may be used for reverse geocoding.
- Map imagery may be retrieved from the configured map provider.

Use of these services may be subject to their own usage policies and availability.
