"""Before/after preview dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QHBoxLayout


class PreviewDialog(QDialog):
    """Simple zoomable preview for a source image."""

    def __init__(self, image_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Preview - {image_path.name}")
        self.resize(1000, 700)
        layout = QHBoxLayout(self)
        self.view = QGraphicsView()
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        scene = QGraphicsScene(self.view)
        item = QGraphicsPixmapItem(QPixmap(str(image_path)))
        scene.addItem(item)
        self.view.setScene(scene)
        self.view.fitInView(item, Qt.KeepAspectRatio)
        layout.addWidget(self.view)

    def wheelEvent(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 0.87
        self.view.scale(factor, factor)
