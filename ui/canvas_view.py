# 核心无限画布系统 / Core infinite-canvas reference board view.
import os
import urllib.parse
import urllib.request
from uuid import uuid4

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

from refboard_core.file_manager import FileManager
from refboard_core.constants import SUPPORTED_IMAGE_EXTENSIONS
from ui.image_item import RefImageItem


class RefCanvasView(QtWidgets.QGraphicsView):
    """Infinite-feeling canvas for image references."""

    boardChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super(RefCanvasView, self).__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.scene().setSceneRect(-50000, -50000, 100000, 100000)
        self.setAcceptDrops(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.BoundingRectViewportUpdate)
        self.setBackgroundBrush(QtGui.QColor("#17181a"))
        self.file_manager = FileManager()
        self._panning = False
        self._last_pan_point = QtCore.QPoint()

    def add_image(self, path, scene_pos=None):
        if not path or not os.path.exists(path):
            return None
        pixmap = QtGui.QPixmap(path)
        if pixmap.isNull():
            return None
        item = RefImageItem(pixmap, source_path=os.path.abspath(path))
        if scene_pos is None:
            scene_pos = self.mapToScene(self.viewport().rect().center())
        item.setPos(scene_pos)
        item.setZValue(self._next_z_value())
        self.scene().addItem(item)
        self.scene().clearSelection()
        item.setSelected(True)
        self.boardChanged.emit()
        return item

    def clear_board(self):
        self.scene().clear()
        self.resetTransform()
        self.boardChanged.emit()

    def image_items(self):
        return [item for item in self.scene().items() if isinstance(item, RefImageItem)]

    def dragEnterEvent(self, event):
        if self._event_has_images(event):
            event.acceptProposedAction()
            return
        super(RefCanvasView, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self._event_has_images(event):
            event.acceptProposedAction()
            return
        super(RefCanvasView, self).dragMoveEvent(event)

    def dropEvent(self, event):
        paths = self._image_paths_from_mime(event.mimeData(), download_remote=True)
        image_path = self._save_mime_image(event.mimeData())
        if image_path:
            paths.append(image_path)
        if not paths:
            super(RefCanvasView, self).dropEvent(event)
            return
        base_pos = self.mapToScene(self._event_pos(event))
        for index, path in enumerate(paths):
            self.add_image(path, base_pos + QtCore.QPointF(index * 32, index * 32))
        event.acceptProposedAction()

    def wheelEvent(self, event):
        if event.modifiers() & QtCore.Qt.ControlModifier:
            delta = event.angleDelta().y() if hasattr(event, "angleDelta") else event.delta()
            factor = 1.15 if delta > 0 else 1.0 / 1.15
            self.scale(factor, factor)
            self.boardChanged.emit()
            event.accept()
            return
        super(RefCanvasView, self).wheelEvent(event)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Paste):
            if self.paste_images_from_clipboard():
                event.accept()
                return
        if event.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
            if self.delete_selected_items():
                event.accept()
                return
        if event.key() == QtCore.Qt.Key_Q:
            self.rotate_selected_items(-5.0)
            event.accept()
            return
        if event.key() == QtCore.Qt.Key_E:
            self.rotate_selected_items(5.0)
            event.accept()
            return
        super(RefCanvasView, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton or (
            event.button() == QtCore.Qt.LeftButton and event.modifiers() & QtCore.Qt.AltModifier
        ):
            self._panning = True
            self._last_pan_point = event.pos()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            event.accept()
            return
        super(RefCanvasView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self._last_pan_point)
            self.translate(delta.x(), delta.y())
            self._last_pan_point = event.pos()
            self.boardChanged.emit()
            event.accept()
            return
        super(RefCanvasView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._panning:
            self._panning = False
            self.setCursor(QtCore.Qt.ArrowCursor)
            event.accept()
            return
        super(RefCanvasView, self).mouseReleaseEvent(event)

    def _next_z_value(self):
        values = [item.zValue() for item in self.image_items()]
        return (max(values) + 1) if values else 1

    def _event_has_images(self, event):
        mime = event.mimeData()
        return bool(self._image_paths_from_mime(mime)) or mime.hasImage() or self._mime_has_remote_url(mime)

    def _image_paths_from_mime(self, mime, download_remote=False):
        paths = []
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.splitext(path)[1].lower() in SUPPORTED_IMAGE_EXTENSIONS:
                        paths.append(path)
                elif download_remote:
                    path = self._download_image_url(url.toString())
                    if path:
                        paths.append(path)
        if mime.hasText():
            text_path = mime.text().strip().strip('"')
            if self._is_supported_image_path(text_path):
                paths.append(text_path)
            elif download_remote:
                path = self._download_image_url(text_path)
                if path:
                    paths.append(path)
        return paths

    def _event_pos(self, event):
        if hasattr(event, "position"):
            return event.position().toPoint()
        return event.pos()

    def _selected_image_items(self):
        return [item for item in self.scene().selectedItems() if isinstance(item, RefImageItem)]

    def _is_supported_image_path(self, path):
        return (
            bool(path)
            and os.path.exists(path)
            and os.path.splitext(path)[1].lower() in SUPPORTED_IMAGE_EXTENSIONS
        )

    def _mime_has_remote_url(self, mime):
        if mime.hasUrls():
            for url in mime.urls():
                if self._is_remote_url(url.toString()):
                    return True
        return mime.hasText() and self._is_remote_url(mime.text().strip())

    def _is_remote_url(self, url):
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme in ("http", "https")

    def _download_image_url(self, url):
        if not self._is_remote_url(url):
            return None
        parsed = urllib.parse.urlparse(url)
        ext = os.path.splitext(parsed.path)[1].lower()
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "NukeRefBoard/1.0"})
            response = urllib.request.urlopen(request, timeout=8)
            content_type = response.info().get("Content-Type", "")
            data = response.read()
        except Exception:
            return None
        if "image" not in content_type.lower() and ext not in SUPPORTED_IMAGE_EXTENSIONS:
            return None

        if ext not in SUPPORTED_IMAGE_EXTENSIONS:
            ext = ".png"

        asset_dir = self.file_manager.ensure_runtime_dir()
        path = os.path.join(asset_dir, "drop_{0}{1}".format(uuid4().hex[:10], ext))
        with open(path, "wb") as handle:
            handle.write(data)
        return path

    def _save_mime_image(self, mime):
        if not mime.hasImage():
            return None
        image = QtGui.QImage()
        image_data = mime.imageData()
        if isinstance(image_data, QtGui.QPixmap):
            image = image_data.toImage()
        elif isinstance(image_data, QtGui.QImage):
            image = image_data
        if image.isNull():
            return None
        asset_dir = self.file_manager.ensure_runtime_dir()
        path = os.path.join(asset_dir, "paste_{0}.png".format(uuid4().hex[:10]))
        if image.save(path, "PNG"):
            return path
        return None

    def paste_images_from_clipboard(self):
        clipboard = QtWidgets.QApplication.clipboard()
        mime = clipboard.mimeData()
        paths = self._image_paths_from_mime(mime)
        image_path = self._save_mime_image(mime)
        if image_path:
            paths.append(image_path)
        if not paths:
            return False

        base_pos = self.mapToScene(self.viewport().rect().center())
        for index, path in enumerate(paths):
            self.add_image(path, base_pos + QtCore.QPointF(index * 32, index * 32))
        return True

    def delete_selected_items(self):
        items = self._selected_image_items()
        if not items:
            return False
        for item in items:
            self.scene().removeItem(item)
        self.boardChanged.emit()
        return True

    def rotate_selected_items(self, angle_delta):
        items = self._selected_image_items()
        if not items:
            return False
        for item in items:
            item.setRotation(item.rotation() + angle_delta)
        self.boardChanged.emit()
        return True
