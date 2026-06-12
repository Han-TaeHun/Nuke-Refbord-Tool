# 무한 캔버스 레퍼런스 보드 뷰
import os
import urllib.parse
import urllib.request
from uuid import uuid4

try:
    from PySide2 import QtCore, QtGui, QtSvg, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtSvg, QtWidgets

try:
    import nuke
except ImportError:  # pragma: no cover - allows local UI testing outside Nuke
    nuke = None

from ..refboard_core.file_manager import FileManager
from ..refboard_core.constants import SUPPORTED_IMAGE_EXTENSIONS
from ..refboard_core.nodemark import list_nodemark_backdrops
from .framejump_item import RefFrameJumpItem
from .image_item import RefImageItem
from .nodemark_dialog import AddNodeMarkDialog
from .nodemark_item import RefNodeMarkItem
from .note_item import RefNoteItem
from .undo_commands import (
    AddBoardItemCommand,
    BringBoardItemsToFrontCommand,
    ItemStateChangeCommand,
    RemoveBoardItemsCommand,
)


class RefCanvasView(QtWidgets.QGraphicsView):
    """Infinite-feeling canvas for image references."""

    boardChanged = QtCore.Signal()
    DEFAULT_TEXT_COLOR = "#f2f2f2"
    DEFAULT_TEXT_BACKGROUND = "#202124"

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
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setOptimizationFlag(QtWidgets.QGraphicsView.DontSavePainterState, False)
        self.setBackgroundBrush(QtGui.QColor("#17181a"))
        self.file_manager = FileManager()
        self._undo_stack = QtWidgets.QUndoStack(self)
        self._undo_limit = 50
        self._undo_stack.setUndoLimit(self._undo_limit)
        self._suspend_undo_tracking = False
        self._icon_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources",
            "icons",
        )
        self._panning = False
        self._last_pan_point = QtCore.QPoint()
        self._pan_sensitivity = 1.0
        self._updating_text_toolbar = False
        self._note_default_font_family = "Verdana"
        self._note_default_font_size = 18
        self._note_default_text_color = self.DEFAULT_TEXT_COLOR
        self._note_default_background_color = self.DEFAULT_TEXT_BACKGROUND
        self._note_default_transparent_background = False
        self._auto_enter_edit_mode_for_new_text = True
        self._continue_checklist_on_new_line = True
        self._nodemark_link_style = "Hyperlink text"
        self._nodemark_missing_behavior = "Show warning"
        self._build_text_toolbar()
        self.scene().selectionChanged.connect(self._update_text_toolbar)
        self.horizontalScrollBar().valueChanged.connect(lambda _: self._update_text_toolbar_position())
        self.verticalScrollBar().valueChanged.connect(lambda _: self._update_text_toolbar_position())

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
        self._wire_item_callbacks(item)
        self._undo_stack.push(AddBoardItemCommand(self, item, "Add Image"))
        return item

    def clear_board(self):
        self.clear_undo_history()
        self.scene().clear()
        self.resetTransform()
        self._notify_scene_changed()

    def image_items(self):
        return [item for item in self.scene().items() if getattr(item, "refboard_item_type", "") == "image"]

    def note_items(self):
        return [item for item in self.scene().items() if getattr(item, "refboard_item_type", "") == "note"]

    def nodemark_items(self):
        return [item for item in self.scene().items() if getattr(item, "refboard_item_type", "") == "nodemark"]

    def framejump_items(self):
        return [item for item in self.scene().items() if getattr(item, "refboard_item_type", "") == "framejump"]

    def add_note(self, scene_pos=None, text="Text"):
        if scene_pos is None:
            scene_pos = self.mapToScene(self.viewport().rect().center())
        item = RefNoteItem(text)
        self._wire_note_item(item)
        self._wire_item_callbacks(item)
        item.setPos(scene_pos)
        item.setZValue(self._next_z_value())
        self._undo_stack.push(AddBoardItemCommand(self, item, "Add Text"))
        try:
            self._apply_note_defaults(item)
        except Exception:
            pass
        self._activate_new_note(item)
        self.viewport().update()
        return item

    def add_nodemark_link(self, backdrop_name, label, scene_pos=None):
        if scene_pos is None:
            scene_pos = self.mapToScene(self.viewport().rect().center())
        item = RefNodeMarkItem(backdrop_name, label)
        self._apply_nodemark_item_settings(item)
        self._wire_item_callbacks(item)
        item.setPos(scene_pos)
        item.setZValue(self._next_z_value())
        self._undo_stack.push(AddBoardItemCommand(self, item, "Add NodeMark"))
        return item

    def add_framejump_link(self, frame, label, scene_pos=None):
        if scene_pos is None:
            scene_pos = self.mapToScene(self.viewport().rect().center())
        item = RefFrameJumpItem(frame, label)
        self._wire_item_callbacks(item)
        item.setPos(scene_pos)
        item.setZValue(self._next_z_value())
        self._undo_stack.push(AddBoardItemCommand(self, item, "Add Frame Jump"))
        return item

    def board_model(self):
        center = self.mapToScene(self.viewport().rect().center())
        transform = self.transform()
        zoom = float(transform.m11()) if transform.m11() else 1.0
        from ..models.board_model import BoardModel

        return BoardModel(
            zoom=zoom,
            offset_x=center.x(),
            offset_y=center.y(),
        )

    def image_models(self):
        return [item.to_model() for item in self.image_items()]

    def note_models(self):
        return [item.to_model() for item in self.note_items()]

    def nodemark_models(self):
        return [item.to_model() for item in self.nodemark_items()]

    def framejump_models(self):
        return [item.to_model() for item in self.framejump_items()]

    def load_board(self, board_model, image_models, note_models=None, nodemark_models=None, framejump_models=None):
        self.clear_board()
        max_image_z = 0
        self._suspend_undo_tracking = True
        for model in image_models or []:
            if not model.file or not os.path.exists(model.file):
                continue
            pixmap = QtGui.QPixmap(model.file)
            if pixmap.isNull():
                continue
            item = RefImageItem.from_model(model, pixmap)
            self._wire_item_callbacks(item)
            self.scene().addItem(item)
            max_image_z = max(max_image_z, int(item.zValue()))
        for model in note_models or []:
            item = RefNoteItem.from_model(model)
            item.set_continue_checklist_on_new_line(self._continue_checklist_on_new_line)
            self._wire_note_item(item)
            self._wire_item_callbacks(item)
            item.setZValue(max(max_image_z + 1, item.zValue()))
            self.scene().addItem(item)
            max_image_z = max(max_image_z, int(item.zValue()))
        for model in nodemark_models or []:
            item = RefNodeMarkItem.from_model(model)
            self._apply_nodemark_item_settings(item)
            self._wire_item_callbacks(item)
            item.setZValue(max(max_image_z + 1, item.zValue()))
            self.scene().addItem(item)
            max_image_z = max(max_image_z, int(item.zValue()))
        for model in framejump_models or []:
            item = RefFrameJumpItem.from_model(model)
            self._wire_item_callbacks(item)
            item.setZValue(max(max_image_z + 1, item.zValue()))
            self.scene().addItem(item)
            max_image_z = max(max_image_z, int(item.zValue()))
        self._suspend_undo_tracking = False

        self._restore_board_view(board_model)
        self.clear_undo_history()
        self._notify_scene_changed()

    def current_note_item(self):
        focus_item = self.scene().focusItem()
        if getattr(focus_item, "refboard_item_type", "") == "note":
            return focus_item
        selected_notes = [
            item for item in self.scene().selectedItems() if getattr(item, "refboard_item_type", "") == "note"
        ]
        return selected_notes[0] if selected_notes else None

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
        if self._updating_text_toolbar:
            return False
        note = self.current_note_item()
        if note is None:
            return False
        note.apply_text_format(
            bold=bold,
            italic=italic,
            underline=underline,
            strike_out=strike_out,
            point_size=point_size,
            font_family=font_family,
            text_color=text_color,
            background_color=background_color,
        )
        self.boardChanged.emit()
        self._sync_text_toolbar_state(note)
        self._update_text_toolbar_position()
        return True

    def apply_settings(self, settings):
        settings = settings or {}
        self._note_default_font_family = settings.get("default_note_font_family", "Verdana")
        self._note_default_font_size = int(settings.get("default_note_font_size", 18) or 18)
        self._note_default_text_color = settings.get("default_note_text_color", self.DEFAULT_TEXT_COLOR)
        self._note_default_background_color = settings.get(
            "default_note_background_color",
            self.DEFAULT_TEXT_BACKGROUND,
        )
        self._note_default_transparent_background = bool(
            settings.get("default_note_transparent_background")
        )
        self._auto_enter_edit_mode_for_new_text = bool(
            settings.get("auto_enter_edit_mode_for_new_text", True)
        )
        self._continue_checklist_on_new_line = bool(
            settings.get("continue_checklist_on_new_line", True)
        )
        self._nodemark_link_style = settings.get("nodemark_link_style", "Hyperlink text")
        self._nodemark_missing_behavior = settings.get("nodemark_missing_behavior", "Show warning")
        self.DEFAULT_TEXT_COLOR = self._note_default_text_color
        self.DEFAULT_TEXT_BACKGROUND = (
            "transparent"
            if self._note_default_transparent_background
            else self._note_default_background_color
        )
        for item in self.note_items():
            item.set_continue_checklist_on_new_line(self._continue_checklist_on_new_line)
        for item in self.nodemark_items():
            self._apply_nodemark_item_settings(item)
        self._update_text_toolbar()
        self.viewport().update()

    def resizeEvent(self, event):
        super(RefCanvasView, self).resizeEvent(event)
        self._update_text_toolbar_position()

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
        paths = self._image_paths_from_mime(event.mimeData(), download_remote=True, include_image_data=True)
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
            self._update_text_toolbar_position()
            event.accept()
            return
        super(RefCanvasView, self).wheelEvent(event)

    def keyPressEvent(self, event):
        if self._text_item_is_editing():
            super(RefCanvasView, self).keyPressEvent(event)
            return
        if event.matches(QtGui.QKeySequence.Undo):
            if self.undo_last_action():
                event.accept()
                return
        if event.matches(QtGui.QKeySequence.Paste):
            if self.paste_from_clipboard():
                event.accept()
                return
        if event.matches(QtGui.QKeySequence.Copy):
            if self.copy_selected_content_to_clipboard():
                event.accept()
                return
        if event.key() == QtCore.Qt.Key_F:
            if self.frame_selected_or_all_images():
                event.accept()
                return
        if event.key() == QtCore.Qt.Key_Delete:
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
            self._last_pan_point = self._event_pos(event)
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            event.accept()
            return
        super(RefCanvasView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            current_pos = self._event_pos(event)
            delta = current_pos - self._last_pan_point
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x() * self._pan_sensitivity)
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y() * self._pan_sensitivity)
            )
            self._last_pan_point = current_pos
            self.boardChanged.emit()
            event.accept()
            return
        super(RefCanvasView, self).mouseMoveEvent(event)
        self._update_text_toolbar_position()

    def mouseReleaseEvent(self, event):
        if self._panning:
            self._panning = False
            self.setCursor(QtCore.Qt.ArrowCursor)
            event.accept()
            return
        super(RefCanvasView, self).mouseReleaseEvent(event)
        self._update_text_toolbar_position()

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        new_text_action = menu.addAction("New Text")
        new_checklist_action = menu.addAction("New Checklist")
        add_nodemark_action = menu.addAction("Add NodeMark")
        add_framejump_action = menu.addAction("Add Current Frame")
        menu.addSeparator()
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        undo_action = menu.addAction("Undo")
        bring_to_front_action = menu.addAction("Bring to Front")
        menu.addSeparator()
        settings_action = menu.addAction("Settings")

        copy_action.setEnabled(self._can_copy_selected_content())
        paste_action.setEnabled(self._can_paste_from_clipboard())
        undo_action.setEnabled(self._undo_stack.canUndo())
        bring_to_front_action.setEnabled(bool(self._selected_board_items()))

        debug_menu = None
        test_loading_action = None
        hide_loading_action = None
        test_save_toast_action = None
        test_save_error_toast_action = None
        hide_save_toast_action = None
        if self._debug_mode_enabled():
            menu.addSeparator()
            debug_menu = menu.addMenu("Dev Debug Test")
            test_loading_action = debug_menu.addAction("Test Loading Overlay")
            hide_loading_action = debug_menu.addAction("Hide Loading Overlay")
            debug_menu.addSeparator()
            test_save_toast_action = debug_menu.addAction("Test Save Toast")
            test_save_error_toast_action = debug_menu.addAction("Test Save Failed Toast")
            hide_save_toast_action = debug_menu.addAction("Hide Save Toast")

        action = menu.exec_(event.globalPos())
        if action is None:
            return
        if action == new_text_action:
            self.add_note(self.mapToScene(event.pos()))
        elif action == new_checklist_action:
            self.add_checklist(self.mapToScene(event.pos()))
        elif action == add_nodemark_action:
            self._prompt_add_nodemark(self.mapToScene(event.pos()))
        elif action == add_framejump_action:
            self._add_current_frame_jump(self.mapToScene(event.pos()))
        elif action == copy_action:
            self.copy_selected_content_to_clipboard()
        elif action == paste_action:
            self.paste_from_clipboard()
        elif action == undo_action:
            self.undo_last_action()
        elif action == bring_to_front_action:
            self.bring_selected_items_to_front()
        elif action == settings_action:
            panel = self.window()
            if hasattr(panel, "open_settings_dialog"):
                panel.open_settings_dialog()
        elif action == test_loading_action:
            panel = self.window()
            if hasattr(panel, "loading_overlay"):
                panel.loading_overlay.show_centered()
        elif action == hide_loading_action:
            panel = self.window()
            if hasattr(panel, "loading_overlay"):
                panel.loading_overlay.hide()
        elif action == test_save_toast_action:
            panel = self.window()
            if hasattr(panel, "save_toast"):
                panel.save_toast.show_bottom_left("RefBoard saved")
        elif action == test_save_error_toast_action:
            panel = self.window()
            if hasattr(panel, "save_toast"):
                panel.save_toast.show_error_bottom_left("RefBoard save failed")
        elif action == hide_save_toast_action:
            panel = self.window()
            if hasattr(panel, "save_toast"):
                panel.save_toast.hide()

    def _build_text_toolbar(self):
        self.text_toolbar = QtWidgets.QFrame(self.viewport())
        self.text_toolbar.setObjectName("RefBoardFloatingTextToolbar")
        self.text_toolbar.setFixedHeight(40)
        self.text_toolbar.hide()

        layout = QtWidgets.QHBoxLayout(self.text_toolbar)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(5)

        self.text_color_button = self._color_tool_button("A", "Text color")
        self.text_background_button = self._color_tool_button("BG", "Text background color")
        self.text_bold_button = self._floating_tool_button("B", "Bold")
        self.text_italic_button = self._floating_tool_button("I", "Italic")
        self.text_underline_button = self._floating_tool_button("U", "Underline")
        self.text_strike_button = self._floating_tool_button("S", "Strikethrough")
        self.text_checklist_button = self._action_tool_button("Todo", "Insert checklist item", 46)
        self._set_text_toolbar_icon(self.text_color_button, "icon_Text_Character.svg")
        self._set_text_toolbar_icon(self.text_bold_button, "icon_Text_Blod.svg")
        self._set_text_toolbar_icon(self.text_italic_button, "icon_Text_Italic.svg")
        self._set_text_toolbar_icon(self.text_underline_button, "icon_Text_Underline.svg")
        self._set_text_toolbar_icon(self.text_strike_button, "icon_Text_Strikethrough.svg")
        self._set_text_toolbar_icon(self.text_checklist_button, "icon_Text_todo.svg")

        self.text_font_box = QtWidgets.QFontComboBox(self.text_toolbar)
        self.text_font_box.setObjectName("RefBoardFontComboBox")
        self.text_font_box.setFixedWidth(150)

        self.text_size_box = QtWidgets.QSpinBox(self.text_toolbar)
        self.text_size_box.setObjectName("RefBoardFontSizeBox")
        self.text_size_box.setRange(6, 144)
        self.text_size_box.setValue(18)
        self.text_size_box.setFixedWidth(62)
        self.text_size_box.setToolTip("Font size")

        layout.addWidget(self.text_color_button)
        layout.addWidget(self.text_background_button)
        layout.addSpacing(2)
        layout.addWidget(self.text_bold_button)
        layout.addWidget(self.text_italic_button)
        layout.addWidget(self.text_underline_button)
        layout.addWidget(self.text_strike_button)
        layout.addWidget(self.text_checklist_button)
        layout.addSpacing(4)
        layout.addWidget(self.text_font_box)
        layout.addWidget(self.text_size_box)

        self.text_toolbar.adjustSize()
        self.text_color_button.clicked.connect(lambda: self._pick_text_color("foreground"))
        self.text_background_button.clicked.connect(self._show_background_color_menu)
        self.text_bold_button.clicked.connect(
            lambda: self.apply_text_format(bold=self.text_bold_button.isChecked())
        )
        self.text_italic_button.clicked.connect(
            lambda: self.apply_text_format(italic=self.text_italic_button.isChecked())
        )
        self.text_underline_button.clicked.connect(
            lambda: self.apply_text_format(underline=self.text_underline_button.isChecked())
        )
        self.text_strike_button.clicked.connect(
            lambda: self.apply_text_format(strike_out=self.text_strike_button.isChecked())
        )
        self.text_checklist_button.clicked.connect(self.insert_checklist_item)
        self.text_font_box.currentFontChanged.connect(
            lambda font: self.apply_text_format(font_family=font.family())
        )
        self.text_size_box.valueChanged.connect(lambda value: self.apply_text_format(point_size=value))

    def _floating_tool_button(self, label, tooltip):
        button = QtWidgets.QToolButton(self.text_toolbar)
        button.setText(label)
        button.setToolTip(tooltip)
        button.setCheckable(True)
        button.setFixedSize(QtCore.QSize(28, 26))
        return button

    def _color_tool_button(self, label, tooltip):
        button = QtWidgets.QToolButton(self.text_toolbar)
        button.setText(label)
        button.setToolTip(tooltip)
        button.setFixedSize(QtCore.QSize(36, 26))
        return button

    def _action_tool_button(self, label, tooltip, width):
        button = QtWidgets.QToolButton(self.text_toolbar)
        button.setText(label)
        button.setToolTip(tooltip)
        button.setCheckable(False)
        button.setFixedSize(QtCore.QSize(width, 26))
        return button

    def _set_text_toolbar_icon(self, button, icon_name):
        icon_path = os.path.join(self._icon_dir, icon_name)
        if not os.path.exists(icon_path):
            return
        button._refboard_icon_name = icon_name
        button.setIcon(QtGui.QIcon(icon_path))
        button.setIconSize(QtCore.QSize(16, 16))
        button.setText("")
        button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)

    def _set_tinted_svg_icon(self, button, icon_name, color):
        icon_path = os.path.join(self._icon_dir, icon_name)
        if not os.path.exists(icon_path):
            return
        renderer = QtSvg.QSvgRenderer(icon_path)
        if not renderer.isValid():
            return
        size = QtCore.QSize(16, 16)
        pixmap = QtGui.QPixmap(size)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        renderer.render(painter, QtCore.QRectF(0, 0, size.width(), size.height()))
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()
        button.setIcon(QtGui.QIcon(pixmap))
        button.setIconSize(size)

    def _update_text_toolbar(self):
        note = self.current_note_item()
        if note is None:
            self.text_toolbar.hide()
            return
        self._sync_text_toolbar_state(note)
        self._update_text_toolbar_position()
        self.text_toolbar.show()
        self.text_toolbar.raise_()

    def _update_text_toolbar_position(self):
        if not hasattr(self, "text_toolbar") or not self.text_toolbar.isVisible():
            return
        note = self.current_note_item()
        if note is None:
            self.text_toolbar.hide()
            return
        scene_rect = note.mapToScene(note.text_bounding_rect()).boundingRect()
        top_center = self.mapFromScene(scene_rect.center().x(), scene_rect.top())
        x = int(top_center.x() - self.text_toolbar.width() * 0.5)
        y = int(top_center.y() - self.text_toolbar.height() - 10)
        x = max(8, min(x, self.viewport().width() - self.text_toolbar.width() - 8))
        y = max(8, y)
        self.text_toolbar.move(x, y)
        self.text_toolbar.raise_()

    def _sync_text_toolbar_state(self, note):
        if self._updating_text_toolbar:
            return
        self._updating_text_toolbar = True
        char_format = note.current_text_format()
        font = char_format.font()
        self.text_bold_button.setChecked(font.bold())
        self.text_italic_button.setChecked(font.italic())
        self.text_underline_button.setChecked(font.underline())
        self.text_strike_button.setChecked(font.strikeOut())
        self.text_font_box.setCurrentFont(font)
        point_size = font.pointSize()
        if point_size <= 0:
            point_size = 18
        self.text_size_box.setValue(point_size)
        self._set_color_button_color(
            self.text_color_button,
            char_format.foreground().color(),
            self.DEFAULT_TEXT_COLOR,
        )
        self._set_color_button_color(
            self.text_background_button,
            char_format.background().color(),
            self.DEFAULT_TEXT_BACKGROUND,
        )
        self._updating_text_toolbar = False

    def drawForeground(self, painter, rect):
        super(RefCanvasView, self).drawForeground(painter, rect)
        if self.image_items() or self.note_items() or self.nodemark_items() or self.framejump_items():
            return
        message = self._empty_state_message()
        if not message:
            return
        painter.save()
        painter.resetTransform()
        painter.setPen(QtGui.QColor("#8a8d94"))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(self.viewport().rect(), QtCore.Qt.AlignCenter, message)
        painter.restore()

    def _empty_state_message(self):
        panel = self.window()
        if panel is not None and hasattr(panel, "empty_state_message"):
            return panel.empty_state_message()
        return u">>> Please drag the image here <<<"


    def _pick_text_color(self, target):
        note = self.current_note_item()
        if note is None:
            return
        char_format = note.current_text_format()
        if target == "foreground":
            current = char_format.foreground().color()
            fallback = self.DEFAULT_TEXT_COLOR
        else:
            current = char_format.background().color()
            fallback = self.DEFAULT_TEXT_BACKGROUND
        if not current.isValid():
            current = QtGui.QColor(fallback)
        color = QtWidgets.QColorDialog.getColor(current, self, "Select Color")
        if not color.isValid():
            return
        if target == "foreground":
            self.apply_text_format(text_color=color.name())
        else:
            self.apply_text_format(background_color=color.name())

    def _show_background_color_menu(self):
        note = self.current_note_item()
        if note is None:
            return
        menu = QtWidgets.QMenu(self)
        transparent_action = menu.addAction("Transparent")
        choose_color_action = menu.addAction("Choose Color...")
        action = menu.exec_(self.text_background_button.mapToGlobal(QtCore.QPoint(0, self.text_background_button.height())))
        if action == transparent_action:
            self.apply_text_format(background_color="transparent")
        elif action == choose_color_action:
            self._pick_text_color("background")

    def _set_color_button_color(self, button, color, fallback):
        swatch = color if isinstance(color, QtGui.QColor) and color.isValid() else QtGui.QColor(fallback)
        if button is self.text_color_button:
            self._set_tinted_svg_icon(button, getattr(button, "_refboard_icon_name", ""), swatch)
            button.setStyleSheet(
                "QToolButton { background: #2a2d33; color: #d9dce2; border: 1px solid #3d4047; border-radius: 4px; }"
                "QToolButton:hover { border: 1px solid #7aaeff; }"
                "QToolButton:pressed { border: 1px solid #4c9aff; }"
            )
            return
        if swatch.alpha() == 0:
            button.setStyleSheet(
                "QToolButton { background: transparent; color: #d9dce2; border: 1px dashed #5d616b; border-radius: 4px; }"
                "QToolButton:hover { border: 1px solid #7aaeff; }"
                "QToolButton:pressed { border: 1px solid #4c9aff; }"
            )
            return
        text_color = "#101114" if swatch.lightness() > 140 else "#f4f4f4"
        button.setStyleSheet(
            "QToolButton {{ background: {0}; color: {1}; border: 1px solid #3d4047; border-radius: 4px; }}"
            "QToolButton:hover {{ border: 1px solid #7aaeff; }}"
            "QToolButton:pressed {{ border: 1px solid #4c9aff; }}".format(
                swatch.name(),
                text_color,
            )
        )

    def _next_z_value(self):
        values = [
            item.zValue()
            for item in self.image_items() + self.note_items() + self.nodemark_items() + self.framejump_items()
        ]
        return (max(values) + 1) if values else 1

    def _wire_note_item(self, item):
        document = item.document()
        if document is None or getattr(item, "_refboard_note_wired", False):
            return
        item.set_continue_checklist_on_new_line(self._continue_checklist_on_new_line)
        document.contentsChanged.connect(self._on_note_contents_changed)
        item._refboard_note_wired = True

    def _wire_item_callbacks(self, item):
        item.on_state_changed = self._on_item_state_changed

    def _on_note_contents_changed(self):
        self._notify_scene_changed()
        self._update_text_toolbar_position()

    def _on_item_state_changed(self, item, before_state, after_state):
        if self._suspend_undo_tracking:
            return
        self._undo_stack.push(
            ItemStateChangeCommand(
                self,
                item,
                before_state,
                after_state,
                "Transform Item" if "rotation" in after_state or "scale" in after_state else "Move Item",
            )
        )

    def insert_checklist_item(self):
        note = self.current_note_item()
        if note is None:
            note = self.add_note(text="")
        note.insert_checklist_item()
        self._notify_scene_changed()
        self._update_text_toolbar()
        self._update_text_toolbar_position()
        return True

    def add_checklist(self, scene_pos=None):
        note = self.add_note(scene_pos=scene_pos, text="")
        note.insert_checklist_item()
        self._notify_scene_changed()
        self._update_text_toolbar()
        self._update_text_toolbar_position()
        return note

    def undo_last_action(self):
        if not self._undo_stack.canUndo():
            return False
        self._undo_stack.undo()
        return True

    def set_max_undo_steps(self, steps):
        limit = max(1, int(steps or 1))
        self._undo_limit = limit
        self._undo_stack.setUndoLimit(limit)
        return limit

    def max_undo_steps(self):
        return self._undo_limit

    def clear_undo_history(self):
        self._undo_stack.clear()

    def _add_item_to_scene(self, item, select=False):
        if getattr(item, "refboard_item_type", "") == "note":
            self._wire_note_item(item)
        self._wire_item_callbacks(item)
        if item.scene() is not self.scene():
            self.scene().addItem(item)
        if select:
            self.scene().clearSelection()
            item.setSelected(True)
        self._notify_scene_changed()

    def _remove_item_from_scene(self, item):
        if item.scene() is self.scene():
            self.scene().removeItem(item)
        self._notify_scene_changed()

    def _apply_item_state(self, item, state):
        if item is None:
            return
        self._suspend_undo_tracking = True
        try:
            if hasattr(item, "apply_state"):
                item.apply_state(state)
        finally:
            self._suspend_undo_tracking = False
        self._notify_scene_changed()

    def _notify_scene_changed(self):
        self.boardChanged.emit()
        self._update_text_toolbar()
        self.viewport().update()

    def _apply_note_defaults(self, item):
        item.set_continue_checklist_on_new_line(self._continue_checklist_on_new_line)
        background = (
            "transparent"
            if self._note_default_transparent_background
            else self._note_default_background_color
        )
        item.apply_text_format(
            font_family=self._note_default_font_family,
            point_size=self._note_default_font_size,
            text_color=self._note_default_text_color,
            background_color=background,
        )

    def _activate_new_note(self, item):
        if item is None or item.scene() is not self.scene():
            return
        self.scene().clearSelection()
        item.setSelected(True)
        self.setFocus(QtCore.Qt.OtherFocusReason)
        self.scene().setFocusItem(item, QtCore.Qt.OtherFocusReason)
        if self._auto_enter_edit_mode_for_new_text:
            item.begin_edit()
        self._update_text_toolbar()
        self._update_text_toolbar_position()

    def _apply_nodemark_item_settings(self, item):
        if item is None:
            return
        item.apply_display_settings(
            link_style=self._nodemark_link_style,
            missing_behavior=self._nodemark_missing_behavior,
        )

    def _event_has_images(self, event):
        mime = event.mimeData()
        return bool(self._image_paths_from_mime(mime)) or mime.hasImage() or self._mime_has_remote_url(mime)

    def _image_paths_from_mime(self, mime, download_remote=False, include_image_data=False):
        paths = []
        remote_urls = []
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.splitext(path)[1].lower() in SUPPORTED_IMAGE_EXTENSIONS:
                        paths.append(path)
                else:
                    remote_urls.append(url.toString())
        if mime.hasText():
            text_path = mime.text().strip().strip('"')
            if self._is_supported_image_path(text_path):
                paths.append(text_path)
            else:
                remote_urls.extend(self._remote_urls_from_text(text_path))
        if download_remote:
            for url in self._dedupe_urls(remote_urls):
                path = self._download_image_url(url)
                if path:
                    paths.append(path)
        if include_image_data and not paths:
            image_path = self._save_mime_image(mime)
            if image_path:
                paths.append(image_path)
        return self._dedupe_paths(paths)

    def _event_pos(self, event):
        if hasattr(event, "position"):
            return event.position().toPoint()
        return event.pos()

    def _dedupe_paths(self, paths):
        unique_paths = []
        seen = set()
        for path in paths:
            normalized = os.path.normcase(os.path.abspath(path))
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_paths.append(path)
        return unique_paths

    def _dedupe_urls(self, urls):
        unique_urls = []
        seen = set()
        for url in urls:
            if not self._is_remote_url(url):
                continue
            normalized = self._normalize_url(url)
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_urls.append(url)
        return unique_urls

    def _remote_urls_from_text(self, text):
        urls = []
        for token in text.replace('"', " ").replace("'", " ").split():
            token = token.strip("()[]<>;,")
            if self._is_remote_url(token):
                urls.append(token)
        if not urls and self._is_remote_url(text):
            urls.append(text)
        return urls

    def _normalize_url(self, url):
        parsed = urllib.parse.urlparse(url.strip())
        return urllib.parse.urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path,
                "",
                parsed.query,
                "",
            )
        )

    def _selected_image_items(self):
        return [item for item in self.scene().selectedItems() if getattr(item, "refboard_item_type", "") == "image"]

    def _selected_board_items(self):
        return [
            item
            for item in self.scene().selectedItems()
            if getattr(item, "refboard_item_type", "") in ("image", "note", "nodemark", "framejump")
        ]

    def _text_item_is_editing(self):
        focus_item = self.scene().focusItem()
        return getattr(focus_item, "refboard_item_type", "") == "note" and focus_item.is_editing()

    def frame_selected_or_all_images(self):
        selected_items = self._selected_board_items()
        return self._frame_items(
            selected_items or (self.image_items() + self.note_items() + self.nodemark_items() + self.framejump_items())
        )

    def frame_all_images(self):
        return self._frame_items(self.image_items() + self.note_items() + self.nodemark_items() + self.framejump_items())

    def _frame_items(self, items):
        if not items:
            self.resetTransform()
            self.centerOn(0, 0)
            self.boardChanged.emit()
            return True

        rect = QtCore.QRectF()
        for item in items:
            if isinstance(item, RefImageItem):
                item_rect = item.mapToScene(item.image_bounding_rect()).boundingRect()
            elif isinstance(item, RefNoteItem):
                item_rect = item.mapToScene(item.text_bounding_rect()).boundingRect()
            else:
                item_rect = item.mapToScene(item.boundingRect()).boundingRect()
            rect = item_rect if rect.isNull() else rect.united(item_rect)
        if rect.isNull() or rect.width() <= 0 or rect.height() <= 0:
            return False

        margin = max(rect.width(), rect.height()) * 0.08
        rect = rect.adjusted(-margin, -margin, margin, margin)
        self.fitInView(rect, QtCore.Qt.KeepAspectRatio)
        self.boardChanged.emit()
        return True

    def _restore_board_view(self, board_model):
        if board_model is None:
            return
        self.resetTransform()
        zoom = max(0.05, min(20.0, float(getattr(board_model, "zoom", 1.0) or 1.0)))
        self.scale(zoom, zoom)
        self.centerOn(float(getattr(board_model, "offset_x", 0.0)), float(getattr(board_model, "offset_y", 0.0)))

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
        paths = self._image_paths_from_mime(mime, include_image_data=True)
        if not paths:
            return False

        base_pos = self.mapToScene(self.viewport().rect().center())
        for index, path in enumerate(paths):
            self.add_image(path, base_pos + QtCore.QPointF(index * 32, index * 32))
        return True

    def paste_from_clipboard(self):
        if self.paste_images_from_clipboard():
            return True
        clipboard = QtWidgets.QApplication.clipboard()
        text = (clipboard.text() or "").strip()
        if not text:
            return False
        self.add_note(text=text)
        return True

    def copy_selected_content_to_clipboard(self):
        selected_items = self._selected_board_items()
        if not selected_items:
            return False

        image_items = [item for item in selected_items if getattr(item, "refboard_item_type", "") == "image"]
        if image_items:
            mime = QtCore.QMimeData()
            urls = []
            text_lines = []
            for item in image_items:
                source_path = getattr(item, "source_path", "")
                if not source_path:
                    continue
                urls.append(QtCore.QUrl.fromLocalFile(source_path))
                text_lines.append(source_path)
            if not urls:
                return False
            mime.setUrls(urls)
            mime.setText("\n".join(text_lines))
            QtWidgets.QApplication.clipboard().setMimeData(mime)
            return True

        text_lines = []
        for item in selected_items:
            item_type = getattr(item, "refboard_item_type", "")
            if item_type in ("note", "nodemark", "framejump"):
                text_lines.append(item.toPlainText())
        if not text_lines:
            return False
        QtWidgets.QApplication.clipboard().setText("\n".join(text_lines))
        return True

    def _can_copy_selected_content(self):
        return bool(self._selected_board_items())

    def _can_paste_from_clipboard(self):
        clipboard = QtWidgets.QApplication.clipboard()
        mime = clipboard.mimeData()
        if self._image_paths_from_mime(mime):
            return True
        if mime.hasImage() or self._mime_has_remote_url(mime):
            return True
        return bool((clipboard.text() or "").strip())

    def _debug_mode_enabled(self):
        panel = self.window()
        if hasattr(panel, "debug_mode_enabled"):
            return bool(panel.debug_mode_enabled())
        return False

    def delete_selected_items(self):
        items = self._selected_board_items()
        if not items:
            return False
        label = "Delete Items" if len(items) > 1 else "Delete Item"
        self._undo_stack.push(RemoveBoardItemsCommand(self, items, label))
        return True

    def bring_selected_items_to_front(self):
        items = self._selected_board_items()
        if not items:
            return False
        label = "Bring Items to Front" if len(items) > 1 else "Bring Item to Front"
        self._undo_stack.push(BringBoardItemsToFrontCommand(self, items, label))
        return True

    def rotate_selected_items(self, angle_delta):
        items = self._selected_image_items()
        if not items:
            return False
        for item in items:
            before_state = item.capture_state()
            after_state = dict(before_state)
            after_state["rotation"] = float(item.rotation() + angle_delta)
            self._undo_stack.push(ItemStateChangeCommand(self, item, before_state, after_state, "Rotate Image"))
        return True

    def _prompt_add_nodemark(self, scene_pos):
        nodemarks = list_nodemark_backdrops()
        if not nodemarks:
            QtWidgets.QMessageBox.information(
                self,
                "No NodeMarks",
                "No backdrop nodes matching the RefBoard NodeMark naming rule were found in this script.",
            )
            return

        label_counts = {}
        for item in nodemarks:
            base_label = item["label"]
            count = label_counts.get(base_label, 0) + 1
            label_counts[base_label] = count
            display_label = base_label if count == 1 else "{0} ({1})".format(base_label, count)
            item["display_label"] = display_label

        dialog = AddNodeMarkDialog(nodemarks, self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        selected_item = dialog.selected_nodemark()
        if not selected_item:
            return

        custom_label = dialog.display_label()
        link_label = custom_label or selected_item["label"]
        self.add_nodemark_link(selected_item["name"], link_label, scene_pos)

    def _add_current_frame_jump(self, scene_pos):
        if nuke is None:
            QtWidgets.QMessageBox.information(
                self,
                "Nuke Unavailable",
                "Current-frame jump links can only be created inside Nuke.",
            )
            return
        try:
            frame = int(nuke.frame())
        except Exception:
            QtWidgets.QMessageBox.information(
                self,
                "Frame Unavailable",
                "The current viewer frame could not be read.",
            )
            return
        self.add_framejump_link(frame, u"→ Frame：{0}".format(frame), scene_pos)
