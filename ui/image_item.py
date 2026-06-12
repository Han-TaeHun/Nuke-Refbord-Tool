# 인터랙티브 레퍼런스 이미지 아이템
import math

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

from ..models.image_model import ImageModel


class RefImageItem(QtWidgets.QGraphicsPixmapItem):
    """Interactive image item used by the reference board scene."""

    HANDLE_SIZE = 12.0
    ROTATE_MARGIN = 20.0

    def __init__(self, pixmap, source_path="", image_id=None, parent=None):
        super().__init__(pixmap, parent)
        self.refboard_item_type = "image"
        self.source_path = source_path
        self.image_id = image_id
        self._interaction_start_state = None
        self.on_state_changed = None
        self._transform_mode = None
        self._drag_start_pos = QtCore.QPointF()
        self._drag_start_scale = 1.0
        self._drag_start_rotation = 0.0
        self._drag_start_distance = 1.0
        self._drag_start_angle = 0.0
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setShapeMode(QtWidgets.QGraphicsPixmapItem.BoundingRectShape)
        self.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable
            | QtWidgets.QGraphicsItem.ItemIsSelectable
            | QtWidgets.QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        margin = self.HANDLE_SIZE + self.ROTATE_MARGIN
        return super().boundingRect().adjusted(-margin, -margin, margin, margin)

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def wheelEvent(self, event):
        if self.isSelected():
            delta = event.delta() if hasattr(event, "delta") else event.angleDelta().y()
            factor = 1.1 if delta > 0 else 1.0 / 1.1
            self.setScale(max(0.05, min(20.0, self.scale() * factor)))
            event.accept()
            return
        super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._interaction_start_state = self.capture_state()
        if self.isSelected() and event.button() == QtCore.Qt.LeftButton:
            handle_name = self._handle_at(event.pos())
            if handle_name:
                self._begin_transform(event.pos(), "scale")
                event.accept()
                return
            if self._rotation_zone_at(event.pos()):
                self._begin_transform(event.pos(), "rotate")
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._transform_mode == "scale":
            self._update_scale(event.pos())
            event.accept()
            return
        if self._transform_mode == "rotate":
            self._update_rotation(event.pos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._transform_mode:
            self._transform_mode = None
            self._notify_state_change()
            event.accept()
            return
        super().mouseReleaseEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self._notify_state_change()

    def hoverMoveEvent(self, event):
        if self.isSelected():
            if self._handle_at(event.pos()):
                self.setCursor(QtCore.Qt.SizeFDiagCursor)
                return
            if self._rotation_zone_at(event.pos()):
                self.setCursor(QtCore.Qt.CrossCursor)
                return
        self.unsetCursor()
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.save()
            pen = QtGui.QPen(QtGui.QColor("#4c9aff"), 2.0)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            image_rect = super().boundingRect()
            painter.drawRect(image_rect)
            painter.setBrush(QtGui.QColor("#202124"))
            for handle_rect in self._handle_rects().values():
                painter.drawRect(handle_rect)
            painter.restore()

    def to_model(self):
        return ImageModel(
            id=self.image_id or "",
            file=self.source_path,
            x=self.pos().x(),
            y=self.pos().y(),
            scale=self.scale(),
            rotation=self.rotation(),
            z_order=int(self.zValue()),
        )

    @classmethod
    def from_model(cls, model, pixmap):
        item = cls(pixmap, source_path=model.file, image_id=model.id)
        item.setPos(model.x, model.y)
        item.setScale(model.scale)
        item.setRotation(model.rotation)
        item.setZValue(model.z_order)
        return item

    def image_bounding_rect(self):
        return super().boundingRect()

    def capture_state(self):
        return {
            "x": float(self.pos().x()),
            "y": float(self.pos().y()),
            "scale": float(self.scale()),
            "rotation": float(self.rotation()),
        }

    def apply_state(self, state):
        state = state or {}
        self.setPos(float(state.get("x", self.pos().x())), float(state.get("y", self.pos().y())))
        self.setScale(float(state.get("scale", self.scale())))
        self.setRotation(float(state.get("rotation", self.rotation())))

    def _notify_state_change(self):
        before_state = self._interaction_start_state
        self._interaction_start_state = None
        if before_state is None:
            return
        after_state = self.capture_state()
        if self._states_match(before_state, after_state):
            return
        if callable(self.on_state_changed):
            self.on_state_changed(self, before_state, after_state)

    def _states_match(self, before_state, after_state):
        keys = ("x", "y", "scale", "rotation")
        for key in keys:
            if abs(float(before_state.get(key, 0.0)) - float(after_state.get(key, 0.0))) > 0.001:
                return False
        return True

    def _begin_transform(self, item_pos, mode):
        center = self.transformOriginPoint()
        self._transform_mode = mode
        self._drag_start_pos = item_pos
        self._drag_start_scale = self.scale()
        self._drag_start_rotation = self.rotation()
        self._drag_start_distance = max(1.0, self._distance(center, item_pos))
        self._drag_start_angle = self._angle(center, item_pos)

    def _update_scale(self, item_pos):
        center = self.transformOriginPoint()
        distance = max(1.0, self._distance(center, item_pos))
        factor = distance / self._drag_start_distance
        self.setScale(max(0.05, min(20.0, self._drag_start_scale * factor)))

    def _update_rotation(self, item_pos):
        center = self.transformOriginPoint()
        angle_delta = self._angle(center, item_pos) - self._drag_start_angle
        self.setRotation(self._drag_start_rotation + angle_delta)

    def _handle_rects(self):
        image_rect = self.image_bounding_rect()
        half = self.HANDLE_SIZE * 0.5
        corners = {
            "top_left": image_rect.topLeft(),
            "top_right": image_rect.topRight(),
            "bottom_left": image_rect.bottomLeft(),
            "bottom_right": image_rect.bottomRight(),
        }
        return {
            name: QtCore.QRectF(point.x() - half, point.y() - half, self.HANDLE_SIZE, self.HANDLE_SIZE)
            for name, point in corners.items()
        }

    def _handle_at(self, item_pos):
        for name, handle_rect in self._handle_rects().items():
            if handle_rect.contains(item_pos):
                return name
        return None

    def _rotation_zone_at(self, item_pos):
        image_rect = self.image_bounding_rect()
        outer_rect = image_rect.adjusted(
            -self.ROTATE_MARGIN,
            -self.ROTATE_MARGIN,
            self.ROTATE_MARGIN,
            self.ROTATE_MARGIN,
        )
        return outer_rect.contains(item_pos) and not image_rect.contains(item_pos)

    def _distance(self, point_a, point_b):
        delta = point_b - point_a
        return math.sqrt(delta.x() * delta.x() + delta.y() * delta.y())

    def _angle(self, point_a, point_b):
        delta = point_b - point_a
        return math.degrees(math.atan2(delta.y(), delta.x()))
