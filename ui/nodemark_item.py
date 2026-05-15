try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets


class RefNodeMarkItem(QtWidgets.QGraphicsTextItem):
    """Lightweight hyperlink-style item that jumps to a NodeMark backdrop."""

    def __init__(self, backdrop_name, label, parent=None):
        super(RefNodeMarkItem, self).__init__(parent)
        self.backdrop_name = backdrop_name
        self.label = label
        self._pressed = False
        self._press_pos = QtCore.QPointF()
        self.setPlainText(label)
        self.setDefaultTextColor(QtGui.QColor("#7fc8ff"))
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setUnderline(True)
        self.setFont(font)
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable
            | QtWidgets.QGraphicsItem.ItemIsSelectable
            | QtWidgets.QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self._pressed = True
        self._press_pos = event.pos()
        super(RefNodeMarkItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        moved = (event.pos() - self._press_pos).manhattanLength() > 6.0
        super(RefNodeMarkItem, self).mouseReleaseEvent(event)
        if self._pressed and not moved and event.button() == QtCore.Qt.LeftButton:
            self._jump_to_backdrop()
        self._pressed = False

    def hoverEnterEvent(self, event):
        self.setDefaultTextColor(QtGui.QColor("#b7e3ff"))
        super(RefNodeMarkItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setDefaultTextColor(QtGui.QColor("#7fc8ff"))
        super(RefNodeMarkItem, self).hoverLeaveEvent(event)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu()
        jump_action = menu.addAction("Jump to NodeMark")
        remove_action = menu.addAction("Remove Link")
        action = menu.exec_(event.screenPos())
        if action == jump_action:
            self._jump_to_backdrop()
        elif action == remove_action and self.scene() is not None:
            self.scene().removeItem(self)
        event.accept()

    def _jump_to_backdrop(self):
        from refboard_core.nodemark import jump_to_nodemark

        if jump_to_nodemark(self.backdrop_name):
            return
        QtWidgets.QMessageBox.information(
            None,
            "NodeMark Missing",
            "This NodeMark backdrop could not be found in the current script.",
        )
