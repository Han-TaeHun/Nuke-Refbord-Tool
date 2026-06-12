# NodeMark 超链接画布元素 / Hyperlink-style NodeMark canvas item.
try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

from ..models.nodemark_model import NodeMarkModel


class RefNodeMarkItem(QtWidgets.QGraphicsTextItem):
    """Lightweight hyperlink-style item that jumps to a NodeMark backdrop."""

    PILL_PADDING_X = 10.0
    PILL_PADDING_Y = 4.0

    def __init__(self, backdrop_name, label, parent=None):
        super(RefNodeMarkItem, self).__init__(parent)
        self.refboard_item_type = "nodemark"
        self.backdrop_name = backdrop_name
        self.label = label
        self._link_style = "Hyperlink text"
        self._missing_behavior = "Show warning"
        self._hovered = False
        self._interaction_start_state = None
        self.on_state_changed = None
        self._pressed = False
        self._press_pos = QtCore.QPointF()
        self._press_scene_pos = QtCore.QPointF()
        self.setPlainText(label)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.setFont(font)
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable
            | QtWidgets.QGraphicsItem.ItemIsSelectable
            | QtWidgets.QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.apply_display_settings()

    def boundingRect(self):
        rect = super(RefNodeMarkItem, self).boundingRect()
        if self._is_pill_style():
            return rect.adjusted(
                -self.PILL_PADDING_X,
                -self.PILL_PADDING_Y,
                self.PILL_PADDING_X,
                self.PILL_PADDING_Y,
            )
        return rect

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._interaction_start_state = self.capture_state()
        self._pressed = True
        self._press_pos = event.pos()
        self._press_scene_pos = event.scenePos()
        super(RefNodeMarkItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        moved = (event.scenePos() - self._press_scene_pos).manhattanLength() > 6.0
        super(RefNodeMarkItem, self).mouseReleaseEvent(event)
        if self._pressed and not moved and event.button() == QtCore.Qt.LeftButton:
            self._jump_to_backdrop()
        self._pressed = False
        if event.button() == QtCore.Qt.LeftButton:
            self._notify_state_change()

    def hoverEnterEvent(self, event):
        self._hovered = True
        self._refresh_style()
        super(RefNodeMarkItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self._refresh_style()
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
        from ..refboard_core.nodemark import jump_to_nodemark

        if jump_to_nodemark(self.backdrop_name):
            return
        if self._missing_behavior == "Show warning":
            QtWidgets.QMessageBox.information(
                None,
                "NodeMark Missing",
                "This NodeMark backdrop could not be found in the current script.\n\n"
                "It may have been deleted, renamed, or the board may belong to another Nuke script.",
            )

    def to_model(self):
        return NodeMarkModel(
            backdrop_name=self.backdrop_name,
            display_label=self.toPlainText(),
            x=self.pos().x(),
            y=self.pos().y(),
            z_order=int(self.zValue()),
        )

    @classmethod
    def from_model(cls, model):
        item = cls(model.backdrop_name, model.display_label)
        item.setPos(model.x, model.y)
        item.setZValue(model.z_order)
        return item

    def capture_state(self):
        return {
            "x": float(self.pos().x()),
            "y": float(self.pos().y()),
        }

    def apply_state(self, state):
        state = state or {}
        self.setPos(float(state.get("x", self.pos().x())), float(state.get("y", self.pos().y())))

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
        keys = ("x", "y")
        for key in keys:
            if abs(float(before_state.get(key, 0.0)) - float(after_state.get(key, 0.0))) > 0.001:
                return False
        return True

    def apply_display_settings(self, link_style=None, missing_behavior=None):
        if link_style is not None:
            self._link_style = link_style
        if missing_behavior is not None:
            self._missing_behavior = missing_behavior
        self.prepareGeometryChange()
        self._refresh_style()
        self.update()

    def paint(self, painter, option, widget=None):
        if self._is_pill_style():
            painter.save()
            rect = self.boundingRect()
            fill = QtGui.QColor("#3b5970") if not self._hovered else QtGui.QColor("#476a84")
            border = QtGui.QColor("#5e86a3")
            painter.setPen(QtGui.QPen(border, 1.0))
            painter.setBrush(fill)
            painter.drawRoundedRect(rect, 8.0, 8.0)
            painter.restore()
        super(RefNodeMarkItem, self).paint(painter, option, widget)

    def _is_pill_style(self):
        return self._link_style == "Pill button"

    def _refresh_style(self):
        font = QtGui.QFont(self.font())
        if self._is_pill_style():
            font.setUnderline(False)
            font.setBold(True)
            self.setDefaultTextColor(QtGui.QColor("#f3f6fb"))
        else:
            font.setUnderline(True)
            font.setBold(False)
            self.setDefaultTextColor(QtGui.QColor("#b7e3ff" if self._hovered else "#7fc8ff"))
        self.setFont(font)
