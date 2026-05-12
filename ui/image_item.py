# 单张参考图片对象 / Interactive reference image item.
try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

from models.image_model import ImageModel


class RefImageItem(QtWidgets.QGraphicsPixmapItem):
    """Interactive image item used by the reference board scene."""

    def __init__(self, pixmap, source_path="", image_id=None, parent=None):
        super(RefImageItem, self).__init__(pixmap, parent)
        self.source_path = source_path
        self.image_id = image_id
        self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setShapeMode(QtWidgets.QGraphicsPixmapItem.BoundingRectShape)
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable
            | QtWidgets.QGraphicsItem.ItemIsSelectable
            | QtWidgets.QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

    def wheelEvent(self, event):
        if self.isSelected():
            factor = 1.1 if event.delta() > 0 else 1.0 / 1.1
            self.setScale(max(0.05, min(20.0, self.scale() * factor)))
            event.accept()
            return
        super(RefImageItem, self).wheelEvent(event)

    def paint(self, painter, option, widget=None):
        super(RefImageItem, self).paint(painter, option, widget)
        if self.isSelected():
            painter.save()
            pen = QtGui.QPen(QtGui.QColor("#4c9aff"), 2.0)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(self.boundingRect())
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
