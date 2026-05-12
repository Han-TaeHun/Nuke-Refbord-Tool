# 文字注释图元 / Editable text annotation graphics item.
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

    def __init__(self, text="Text", note_id=None, parent=None):
        super(RefNoteItem, self).__init__(text, parent)
        self.note_id = note_id
        self._editing = False
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
        self.setTextWidth(240)
        self.setCacheMode(QtWidgets.QGraphicsItem.NoCache)

    def boundingRect(self):
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
        self.update()

    def inputMethodEvent(self, event):
        super(RefNoteItem, self).inputMethodEvent(event)
        self.update()

    def paint(self, painter, option, widget=None):
        if self.isSelected() or self.is_editing() or not self.toPlainText():
            painter.save()
            rect = self.boundingRect()
            pen_color = QtGui.QColor("#4c9aff") if self.isSelected() or self.is_editing() else QtGui.QColor("#5a5d66")
            painter.setPen(QtGui.QPen(pen_color, 1.5))
            painter.setBrush(QtGui.QColor(32, 33, 36, 180))
            painter.drawRect(rect)
            painter.restore()
        super(RefNoteItem, self).paint(painter, option, widget)

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
