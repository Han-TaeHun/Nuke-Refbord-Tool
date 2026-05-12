# 核心无限画布系统 / Core infinite-canvas reference board view.
import os

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

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
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.BoundingRectViewportUpdate)
        self.setBackgroundBrush(QtGui.QColor("#17181a"))
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
        paths = self._image_paths_from_event(event)
        if not paths:
            super(RefCanvasView, self).dropEvent(event)
            return
        base_pos = self.mapToScene(event.pos())
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
        return bool(self._image_paths_from_event(event))

    def _image_paths_from_event(self, event):
        mime = event.mimeData()
        paths = []
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.splitext(path)[1].lower() in SUPPORTED_IMAGE_EXTENSIONS:
                        paths.append(path)
        return paths
