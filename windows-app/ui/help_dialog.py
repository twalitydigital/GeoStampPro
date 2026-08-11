"""Help and about dialogs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTextBrowser, QVBoxLayout


HELP_HTML = """
<h2>Twality GMark Pro Help</h2>

<h3>Overview</h3>
<p>Twality GMark Pro creates stamped copies of photos while preserving the originals. You can apply Geo Stamping, stamp additional EXIF data, print a watermark, or combine these options in one batch.</p>

<h3>Input and Output Folders</h3>
<ul>
  <li>Choose an input folder or drag a folder into the app.</li>
  <li>The output folder automatically changes to <b>gmark_output</b> inside the selected input folder.</li>
  <li>Stamped files are written as copies. Original images are not modified.</li>
  <li>Use <b>Recursive</b> to include images from subfolders.</li>
</ul>

<h3>Stamping Options</h3>
<ul>
  <li><b>Geo Stamping</b>: prints GPS coordinates, altitude, capture timestamp, camera details, address, and map when GPS metadata is available.</li>
  <li><b>All Additional EXIF Data</b>: prints additional available EXIF fields. Large binary fields such as MakerNote are skipped to keep output readable.</li>
  <li><b>Print Watermark</b>: prints the configured text or image watermark.</li>
</ul>
<p>At least one stamping option must be selected before previewing or processing.</p>

<h3>Geo Stamping Settings</h3>
<ul>
  <li><b>Theme</b>: controls the visual style of the stamp panel.</li>
  <li><b>Placement</b>: places the stamp panel at the top, bottom, left, or right of the photo.</li>
  <li><b>Timestamp format</b>: controls how stamped date/time EXIF fields are displayed.</li>
</ul>

<h3>Watermark Settings</h3>
<ul>
  <li>Open <b>File &gt; Watermark Settings</b> or use the Configure button in the Print Watermark group.</li>
  <li>Select <b>Text</b> to use a text watermark. The image controls are disabled in this mode.</li>
  <li>Select <b>Image</b> to use an image watermark. The text field is disabled in this mode.</li>
  <li>Use the 3x3 position selector to place the watermark.</li>
  <li>Adjust opacity, size, and inset to control watermark appearance.</li>
</ul>

<h3>Preview</h3>
<ul>
  <li>Use <b>File &gt; Preview First Image</b> to render the first matching image with the currently selected options.</li>
  <li>The preview is generated in the app cache and does not modify the source image.</li>
</ul>

<h3>Batch Processing</h3>
<ul>
  <li>Click <b>Start</b> to process the selected input folder.</li>
  <li>The grid shows source path, output path, status, and result message for each image.</li>
  <li>Use <b>Pause</b>, <b>Resume</b>, and <b>Cancel</b> to control an active batch.</li>
</ul>

<h3>GPS and EXIF Behavior</h3>
<ul>
  <li>If Geo Stamping is selected but a photo has no GPS metadata, Geo Stamping is skipped for that photo.</li>
  <li>If All Additional EXIF Data is selected and a GPS-less photo has other EXIF data, the app asks whether to stamp the remaining EXIF data.</li>
  <li>The prompt includes <b>Do this for all items in this batch</b> to apply the same choice to remaining GPS-less photos.</li>
  <li>If no selected option can be applied to a photo, it is skipped with a message explaining why.</li>
</ul>

<h3>Metadata Preservation</h3>
<ul>
  <li>JPEG metadata preservation uses the bundled ExifTool.</li>
  <li>Full metadata preservation is guaranteed only for JPEG outputs.</li>
  <li>For PNG/HEIC/HEIF outputs, the app warns that full EXIF preservation may not be available.</li>
</ul>

<h3>Troubleshooting</h3>
<ul>
  <li><b>No supported images found</b>: confirm the folder contains JPG, JPEG, PNG, HEIC, or HEIF files.</li>
  <li><b>No GPS metadata</b>: the image does not contain GPS coordinates, so Geo Stamping cannot be applied.</li>
  <li><b>ExifTool is required</b>: Twality GMark Pro includes a private ExifTool copy. If that copy is unavailable, the app will also try <b>exiftool.exe</b> from PATH.</li>
  <li><b>Network timeout</b>: address lookup may fail if the reverse geocoding service is unavailable. The app can still stamp coordinates when GPS data exists.</li>
</ul>
"""


ABOUT_HTML = """
<div style="min-width: 420px;">
  <h2>Twality GMark Pro 1.0</h2>
  <p><b>Product Name:</b> Twality GMark Pro 1.0</p>
  <p><b>Company:</b> Twality Digital Solutions LLP</p>
  <p><b>Website:</b> <a href="https://www.twality.com">www.twality.com</a></p>
  <p>Professional photo geo-marking, EXIF stamping, and watermarking utility for Windows.</p>
  <p><b>Metadata Notice:</b> Stamped images are created as output copies. Original source images are not modified.</p>
  <p><b>Disclaimer:</b> GPS, address, map, and EXIF information depend on metadata embedded in the source photo and on availability of external lookup services. Verify output before operational, legal, or archival use.</p>
  <p>Copyright &copy; Twality Digital Solutions LLP. All rights reserved.</p>
</div>
"""


class HelpDialog(QDialog):
    """Scrollable help content."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.resize(760, 620)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML)
        layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class AboutDialog(QDialog):
    """Product information."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Twality GMark Pro")
        layout = QVBoxLayout(self)
        label = QLabel(ABOUT_HTML)
        label.setOpenExternalLinks(True)
        label.setTextInteractionFlags(label.textInteractionFlags() | Qt.TextBrowserInteraction)
        layout.addWidget(label)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
