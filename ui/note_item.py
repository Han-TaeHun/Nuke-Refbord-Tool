# 文字注释图元 / Editable text annotation graphics item.
import math

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

from models.note_model import NoteModel


class RefNoteItem(QtWidgets.QGraphicsTextItem):
    """Editable text note item used by the reference board scene."""

    MIN_WIDTH = 180.0
    MIN_HEIGHT = 42.0
    FRAME_PADDING_X = 6.0
    FRAME_PADDING_Y = 4.0
    HANDLE_SIZE = 12.0
    HANDLE_MARGIN = 10.0

    def __init__(self, text="Text", note_id=None, parent=None):
        super(RefNoteItem, self).__init__(text, parent)
        self.note_id = note_id
        self._editing = False
        self._scaling = False
        self._drag_start_scale = 1.0
        self._drag_start_distance = 1.0
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(False)
        self.setInputMethodHints(QtCore.Qt.ImhNone)
        self.setDefaultTextColor(QtGui.QColor("#f2f2f2"))
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable
            | QtWidgets.QGraphicsItem.ItemIsSelectable
            | QtWidgets.QGraphicsItem.ItemIsFocusable
            | QtWidgets.QGraphicsItem.ItemAcceptsInputMethod
            | QtWidgets.QGraphicsItem.ItemSendsGeometryChanges
        )
        font = QtGui.QFont()
        font.setPointSize(18)
        self.setFont(font)
        self._configure_text_layout()
        self.setTransformOriginPoint(self.text_bounding_rect().center())
        self.setCacheMode(QtWidgets.QGraphicsItem.NoCache)

    def boundingRect(self):
        rect = self.text_bounding_rect()
        handle_margin = self.HANDLE_SIZE + self.HANDLE_MARGIN
        return rect.adjusted(-handle_margin, -handle_margin, handle_margin, handle_margin)

    def text_bounding_rect(self):
        rect = super(RefNoteItem, self).boundingRect()
        rect = rect.united(QtCore.QRectF(0.0, 0.0, self.MIN_WIDTH, self.MIN_HEIGHT))
        return rect.adjusted(
            -self.FRAME_PADDING_X,
            -self.FRAME_PADDING_Y,
            self.FRAME_PADDING_X,
            self.FRAME_PADDING_Y,
        )

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def begin_edit(self):
        self._editing = True
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.setFocus(QtCore.Qt.MouseFocusReason)
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.Document)
        self.setTextCursor(cursor)

    def end_edit(self):
        self._editing = False
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.clearFocus()

    def is_editing(self):
        return self._editing and self.hasFocus()

    def mouseDoubleClickEvent(self, event):
        self.begin_edit()
        event.accept()

    def mousePressEvent(self, event):
        if self.isSelected() and event.button() == QtCore.Qt.LeftButton and self._handle_at(event.pos()):
            self._begin_scale(event.pos())
            event.accept()
            return
        super(RefNoteItem, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._scaling:
            self._update_scale(event.pos())
            event.accept()
            return
        super(RefNoteItem, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._scaling:
            self._scaling = False
            event.accept()
            return
        super(RefNoteItem, self).mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        if self.isSelected() and self._handle_at(event.pos()):
            self.setCursor(QtCore.Qt.SizeFDiagCursor)
            return
        self.unsetCursor()
        super(RefNoteItem, self).hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super(RefNoteItem, self).hoverLeaveEvent(event)

    def focusOutEvent(self, event):
        super(RefNoteItem, self).focusOutEvent(event)
        self._editing = False
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.end_edit()
            event.accept()
            return
        super(RefNoteItem, self).keyPressEvent(event)
        self._configure_text_layout()
        self._update_transform_origin()
        self.update()

    def inputMethodEvent(self, event):
        super(RefNoteItem, self).inputMethodEvent(event)
        self._configure_text_layout()
        self._update_transform_origin()
        self.update()

    def paint(self, painter, option, widget=None):
        if self.isSelected() or self.is_editing() or not self.toPlainText():
            painter.save()
            rect = self.text_bounding_rect()
            pen_color = QtGui.QColor("#4c9aff") if self.isSelected() or self.is_editing() else QtGui.QColor("#5a5d66")
            painter.setPen(QtGui.QPen(pen_color, 1.5))
            painter.setBrush(QtGui.QColor(32, 33, 36, 180))
            painter.drawRect(rect)
            if self.isSelected():
                painter.setBrush(QtGui.QColor("#202124"))
                for handle_rect in self._handle_rects().values():
                    painter.drawRect(handle_rect)
            painter.restore()
        super(RefNoteItem, self).paint(painter, option, widget)

    def apply_text_format(
        self,
        bold=None,
        italic=None,
        underline=None,
        strike_out=None,
        point_size=None,
        font_family=None,
        text_color=None,
        background_color=None,
    ):
        cursor = self.textCursor()
        if not cursor.hasSelection() and not self.is_editing():
            cursor.select(QtGui.QTextCursor.Document)
        char_format = QtGui.QTextCharFormat()
        if bold is not None:
            char_format.setFontWeight(QtGui.QFont.Bold if bold else QtGui.QFont.Normal)
        if italic is not None:
            char_format.setFontItalic(italic)
        if underline is not None:
            char_format.setFontUnderline(underline)
        if strike_out is not None:
            char_format.setFontStrikeOut(strike_out)
        if point_size is not None:
            char_format.setFontPointSize(float(point_size))
        if font_family:
            char_format.setFontFamily(font_family)
        if text_color is not None:
            char_format.setForeground(QtGui.QBrush(QtGui.QColor(text_color)))
        if background_color is not None:
            char_format.setBackground(QtGui.QBrush(QtGui.QColor(background_color)))
        cursor.mergeCharFormat(char_format)
        self.mergeCurrentCharFormat(char_format)
        self.setTextCursor(cursor)
        self._update_transform_origin()
        self.update()

    def current_text_format(self):
        cursor = self.textCursor()
        if cursor.hasSelection() or self.is_editing():
            return cursor.charFormat()

        char_format = QtGui.QTextCharFormat()
        char_format.setFont(self.font())
        char_format.setForeground(QtGui.QBrush(self.defaultTextColor()))
        return char_format

    def current_text_font(self):
        return self.current_text_format().font()

    def to_model(self):
        return NoteModel(
            id=self.note_id or "",
            text=self.toPlainText(),
            x=self.pos().x(),
            y=self.pos().y(),
            z_order=int(self.zValue()),
        )

    @classmethod
    def from_model(cls, model):
        item = cls(text=model.text, note_id=model.id)
        item.setPos(model.x, model.y)
        item.setZValue(model.z_order)
        return item

    def _begin_scale(self, item_pos):
        self._scaling = True
        self._drag_start_scale = self.scale()
        self._drag_start_distance = max(1.0, self._distance(self.transformOriginPoint(), item_pos))

    def _update_scale(self, item_pos):
        distance = max(1.0, self._distance(self.transformOriginPoint(), item_pos))
        factor = distance / self._drag_start_distance
        self.setScale(max(0.05, min(20.0, self._drag_start_scale * factor)))

    def _handle_rects(self):
        rect = self.text_bounding_rect()
        half = self.HANDLE_SIZE * 0.5
        corners = {
            "top_left": rect.topLeft(),
            "top_right": rect.topRight(),
            "bottom_left": rect.bottomLeft(),
            "bottom_right": rect.bottomRight(),
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

    def _distance(self, point_a, point_b):
        delta = point_b - point_a
        return math.sqrt(delta.x() * delta.x() + delta.y() * delta.y())

    def _update_transform_origin(self):
        self.setTransformOriginPoint(self.text_bounding_rect().center())

    def _configure_text_layout(self):
        option = self.document().defaultTextOption()
        option.setWrapMode(QtGui.QTextOption.NoWrap)
        self.document().setDefaultTextOption(option)
        self.setTextWidth(-1)
