# 文字注释图元 / Editable text annotation graphics item.
import math

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

from ..models.note_model import NoteModel


class RefNoteItem(QtWidgets.QGraphicsTextItem):
    """Editable text note item used by the reference board scene."""

    CHECKBOX_UNCHECKED = "[ ] "
    CHECKBOX_CHECKED = "[x] "
    DEFAULT_CANVAS_COLOR = "#17181a"
    MIN_WIDTH = 180.0
    MIN_HEIGHT = 42.0
    FRAME_PADDING_X = 6.0
    FRAME_PADDING_Y = 4.0
    HANDLE_SIZE = 12.0
    HANDLE_MARGIN = 10.0

    def __init__(self, text="Text", note_id=None, parent=None):
        super(RefNoteItem, self).__init__(text, parent)
        self.refboard_item_type = "note"
        self.note_id = note_id
        self._interaction_start_state = None
        self.on_state_changed = None
        self._editing = False
        self._scaling = False
        self._drag_start_scale = 1.0
        self._drag_start_distance = 1.0
        self._continue_checklist_on_new_line = True
        self._base_text_color = QtGui.QColor("#f2f2f2")
        self._base_background_color = QtGui.QColor("#202124")
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(False)
        self.setInputMethodHints(QtCore.Qt.ImhNone)
        self.setDefaultTextColor(self._base_text_color)
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
        if event.button() == QtCore.Qt.LeftButton:
            self._interaction_start_state = self.capture_state()
        if event.button() == QtCore.Qt.LeftButton and self._toggle_checklist_at(event.pos()):
            event.accept()
            return
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
            self._notify_state_change()
            event.accept()
            return
        super(RefNoteItem, self).mouseReleaseEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self._notify_state_change()

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
        insert_checklist_prefix = (
            self.is_editing()
            and self._continue_checklist_on_new_line
            and event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
            and self._current_block_is_checklist()
        )
        super(RefNoteItem, self).keyPressEvent(event)
        if insert_checklist_prefix:
            self.textCursor().insertText(self.CHECKBOX_UNCHECKED)
            cursor = self.textCursor()
            self._apply_checklist_block_style(cursor.block(), False)
            cursor.clearSelection()
            self.setTextCursor(cursor)
        self._configure_text_layout()
        self._update_transform_origin()
        self.update()

    def inputMethodEvent(self, event):
        super(RefNoteItem, self).inputMethodEvent(event)
        self._configure_text_layout()
        self._update_transform_origin()
        self.update()

    def paint(self, painter, option, widget=None):
        if self.isSelected() or self.is_editing():
            painter.save()
            rect = self.text_bounding_rect()
            pen_color = QtGui.QColor("#4c9aff")
            fill_color = QtGui.QColor(32, 33, 36, 200)
            painter.setPen(QtGui.QPen(pen_color, 1.5))
            painter.setBrush(fill_color)
            painter.drawRect(rect)
            if self.isSelected():
                painter.setBrush(QtGui.QColor("#202124"))
                for handle_rect in self._handle_rects().values():
                    painter.drawRect(handle_rect)
            painter.restore()
        super(RefNoteItem, self).paint(painter, option, widget)
        self._paint_checklist_overlays(painter)

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
            color = QtGui.QColor(text_color)
            self._base_text_color = color
            self.setDefaultTextColor(color)
            char_format.setForeground(QtGui.QBrush(color))
        if background_color is not None:
            color = self._parse_background_color(background_color)
            self._base_background_color = color
            char_format.setBackground(QtGui.QBrush(color))
        cursor.mergeCharFormat(char_format)
        self.mergeCurrentCharFormat(char_format)
        self.setTextCursor(cursor)
        updated_font = QtGui.QFont(self.font())
        if bold is not None:
            updated_font.setBold(bool(bold))
        if italic is not None:
            updated_font.setItalic(bool(italic))
        if underline is not None:
            updated_font.setUnderline(bool(underline))
        if strike_out is not None:
            updated_font.setStrikeOut(bool(strike_out))
        if point_size is not None:
            updated_font.setPointSizeF(float(point_size))
        if font_family:
            updated_font.setFamily(font_family)
        self.setFont(updated_font)
        self.document().setDefaultFont(updated_font)
        self._update_transform_origin()
        self.update()

    def current_text_format(self):
        cursor = self.textCursor()
        if cursor.hasSelection() or self.is_editing():
            return cursor.charFormat()

        char_format = QtGui.QTextCharFormat()
        char_format.setFont(self.font())
        char_format.setForeground(QtGui.QBrush(self._base_text_color))
        char_format.setBackground(QtGui.QBrush(self._base_background_color))
        return char_format

    def current_text_font(self):
        return self.current_text_format().font()

    def to_model(self):
        char_format = self.current_text_format()
        font = char_format.font()
        foreground = char_format.foreground().color()
        background = char_format.background().color()
        return NoteModel(
            id=self.note_id or "",
            text=self.toPlainText(),
            x=self.pos().x(),
            y=self.pos().y(),
            z_order=int(self.zValue()),
            style={
                "font_family": font.family(),
                "font_size": font.pointSize() if font.pointSize() > 0 else 18,
                "bold": font.bold(),
                "italic": font.italic(),
                "underline": font.underline(),
                "strike_out": font.strikeOut(),
                "text_color": foreground.name() if foreground.isValid() else "#f2f2f2",
                "background_color": self._serialize_background_color(background),
            },
        )

    @classmethod
    def from_model(cls, model):
        item = cls(text=model.text, note_id=model.id)
        item.setPos(model.x, model.y)
        item.setZValue(model.z_order)
        item._apply_model_style(model.style or {})
        item._configure_text_layout()
        item._restore_checklist_states()
        item._update_transform_origin()
        item.update()
        return item

    def _apply_model_style(self, style):
        font = QtGui.QFont()
        if style.get("font_family"):
            font.setFamily(style.get("font_family"))
        font.setPointSize(int(style.get("font_size", 18) or 18))
        font.setBold(bool(style.get("bold")))
        font.setItalic(bool(style.get("italic")))
        font.setUnderline(bool(style.get("underline")))
        font.setStrikeOut(bool(style.get("strike_out")))
        self.setFont(font)
        self.document().setDefaultFont(font)

        text_color = QtGui.QColor(style.get("text_color") or "#f2f2f2")
        background_color = self._parse_background_color(style.get("background_color"))
        self._base_text_color = QtGui.QColor(text_color)
        self._base_background_color = QtGui.QColor(background_color)
        self.setDefaultTextColor(text_color)

        cursor = QtGui.QTextCursor(self.document())
        cursor.select(QtGui.QTextCursor.Document)
        char_format = QtGui.QTextCharFormat()
        char_format.setFont(font)
        char_format.setForeground(QtGui.QBrush(text_color))
        char_format.setBackground(QtGui.QBrush(background_color))
        cursor.setCharFormat(char_format)

        live_cursor = self.textCursor()
        live_cursor.select(QtGui.QTextCursor.Document)
        live_cursor.setCharFormat(char_format)
        live_cursor.clearSelection()
        self.setTextCursor(live_cursor)
        self.document().adjustSize()

    def insert_checklist_item(self):
        if self.toPlainText().strip() == "Text":
            self.setPlainText("")
        if not self.is_editing():
            self.begin_edit()
        cursor = self.textCursor()
        if self.toPlainText():
            block = cursor.block()
            block_text = block.text() if block.isValid() else ""
            if block_text.strip():
                cursor.movePosition(QtGui.QTextCursor.EndOfBlock)
                cursor.insertBlock()
        cursor.insertText(self.CHECKBOX_UNCHECKED)
        self._apply_checklist_block_style(cursor.block(), False)
        cursor.clearSelection()
        self.setTextCursor(cursor)
        self._configure_text_layout()
        self._update_transform_origin()
        self.update()

    def set_continue_checklist_on_new_line(self, enabled):
        self._continue_checklist_on_new_line = bool(enabled)

    def _toggle_checklist_at(self, item_pos):
        block = self._checklist_block_at(item_pos)
        if not block.isValid():
            return False
        self._set_checklist_block_completed(block, not self._block_is_checked(block))
        self._configure_text_layout()
        self._update_transform_origin()
        self.update()
        return True

    def _checklist_block_at(self, item_pos):
        if item_pos.x() < -self.FRAME_PADDING_X or item_pos.y() < -self.FRAME_PADDING_Y:
            return QtGui.QTextBlock()
        position = self.document().documentLayout().hitTest(item_pos, QtCore.Qt.FuzzyHit)
        if position < 0:
            return QtGui.QTextBlock()
        cursor = QtGui.QTextCursor(self.document())
        cursor.setPosition(position)
        block = cursor.block()
        if not block.isValid() or not self._block_is_checklist(block):
            return QtGui.QTextBlock()
        char_index = max(0, position - block.position())
        if char_index > 2:
            return QtGui.QTextBlock()
        return block

    def _current_block_is_checklist(self):
        block = self.textCursor().block()
        return block.isValid() and self._block_is_checklist(block)

    def _block_is_checklist(self, block):
        if not block.isValid():
            return False
        text = block.text()
        return text.startswith(self.CHECKBOX_UNCHECKED) or text.startswith(self.CHECKBOX_CHECKED)

    def _block_is_checked(self, block):
        return block.isValid() and block.text().startswith(self.CHECKBOX_CHECKED)

    def _set_checklist_block_completed(self, block, completed):
        if not block.isValid() or not self._block_is_checklist(block):
            return
        block_text = block.text()
        if block_text.startswith(self.CHECKBOX_CHECKED):
            content = block_text[len(self.CHECKBOX_CHECKED) :]
        else:
            content = block_text[len(self.CHECKBOX_UNCHECKED) :]
        prefix = self.CHECKBOX_CHECKED if completed else self.CHECKBOX_UNCHECKED

        cursor = QtGui.QTextCursor(block)
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
        cursor.insertText(prefix + content)

        refreshed_block = cursor.block()
        if not refreshed_block.isValid():
            refreshed_block = self.document().findBlock(block.position())
        self._apply_checklist_block_style(refreshed_block, completed)

    def _restore_checklist_states(self):
        block = self.document().firstBlock()
        while block.isValid():
            if self._block_is_checklist(block):
                self._apply_checklist_block_style(block, self._block_is_checked(block))
            block = block.next()

    def _apply_checklist_block_style(self, block, completed):
        if not block.isValid():
            return
        text_color = QtGui.QColor("#8f949c") if completed else QtGui.QColor(self._base_text_color)
        cursor = QtGui.QTextCursor(block)
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
        char_format = QtGui.QTextCharFormat()
        char_format.setFont(self.font())
        char_format.setForeground(QtGui.QBrush(text_color))
        char_format.setBackground(QtGui.QBrush(self._base_background_color))
        char_format.setFontStrikeOut(bool(completed))
        cursor.mergeCharFormat(char_format)

    def _paint_checklist_overlays(self, painter):
        layout = self.document().documentLayout()
        if layout is None:
            return
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        block = self.document().firstBlock()
        while block.isValid():
            if self._block_is_checklist(block):
                block_rect = layout.blockBoundingRect(block)
                self._paint_checklist_prefix_mask(painter, block_rect)
                self._paint_checklist_box(painter, block_rect, self._block_is_checked(block))
            block = block.next()
        painter.restore()

    def _paint_checklist_prefix_mask(self, painter, block_rect):
        prefix_width = QtGui.QFontMetricsF(self.font()).horizontalAdvance(self.CHECKBOX_UNCHECKED) + 2.0
        mask_rect = QtCore.QRectF(0.0, block_rect.top(), prefix_width, block_rect.height())
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(self._mask_background_color()))
        painter.drawRect(mask_rect)

    def _paint_checklist_box(self, painter, block_rect, checked):
        box_size = 14.0
        box_x = 1.0
        box_y = block_rect.top() + max(0.0, (block_rect.height() - box_size) * 0.5)
        box_rect = QtCore.QRectF(box_x, box_y, box_size, box_size)
        if checked:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor("#3b82f6"))
            painter.drawRoundedRect(box_rect, 3.0, 3.0)
            pen = QtGui.QPen(QtGui.QColor("#ffffff"), 1.7)
            painter.setPen(pen)
            tick = QtGui.QPainterPath()
            tick.moveTo(box_rect.left() + 3.2, box_rect.center().y() + 0.2)
            tick.lineTo(box_rect.left() + 6.1, box_rect.bottom() - 3.7)
            tick.lineTo(box_rect.right() - 3.0, box_rect.top() + 3.7)
            painter.drawPath(tick)
            return

        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QPen(QtGui.QColor("#f3f4f6"), 1.2))
        painter.drawRoundedRect(box_rect, 2.8, 2.8)

    def _parse_background_color(self, value):
        if value in (None, "", "default"):
            return QtGui.QColor("#202124")
        if isinstance(value, QtGui.QColor):
            return QtGui.QColor(value)
        if isinstance(value, str) and value.lower() == "transparent":
            return QtGui.QColor(0, 0, 0, 0)
        color = QtGui.QColor(value)
        return color if color.isValid() else QtGui.QColor("#202124")

    def _serialize_background_color(self, color):
        if not isinstance(color, QtGui.QColor) or not color.isValid():
            return "#202124"
        if color.alpha() == 0:
            return "transparent"
        return color.name()

    def _mask_background_color(self):
        if self._base_background_color.alpha() > 0:
            return self._base_background_color
        if self.scene() is not None:
            views = self.scene().views()
            if views:
                brush = views[0].backgroundBrush()
                if brush.style() != QtCore.Qt.NoBrush and brush.color().isValid():
                    return brush.color()
        return QtGui.QColor(self.DEFAULT_CANVAS_COLOR)

    def capture_state(self):
        return {
            "x": float(self.pos().x()),
            "y": float(self.pos().y()),
            "scale": float(self.scale()),
        }

    def apply_state(self, state):
        state = state or {}
        self.setPos(float(state.get("x", self.pos().x())), float(state.get("y", self.pos().y())))
        self.setScale(float(state.get("scale", self.scale())))
        self._update_transform_origin()
        self.update()

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
        keys = ("x", "y", "scale")
        for key in keys:
            if abs(float(before_state.get(key, 0.0)) - float(after_state.get(key, 0.0))) > 0.001:
                return False
        return True

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
