# 主界面控制器 / Main dockable reference board panel controller.
import os
import re

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

try:
    import nuke
except ImportError:  # pragma: no cover - allows local UI testing outside Nuke
    nuke = None

from refboard_core.constants import FILE_EXTENSION, PLUGIN_NAME
from refboard_core.file_manager import FileManager
from refboard_core.serializer import RefBoardSerializer
from session_state import current_settings, update_settings
from ui.canvas_view import RefCanvasView
from ui.settings_dialog import RefBoardSettingsDialog
from ui.status_overlay import RefBoardLoadingOverlay, RefBoardSaveToast
from ui.styles import PANEL_STYLE


class RefBoardPanel(QtWidgets.QWidget):
    """Floating Nuke RefBoard panel with the first interactive canvas."""

    def __init__(self, parent=None):
        super(RefBoardPanel, self).__init__(parent)
        self.setObjectName("NukeRefBoardPanel")
        self.setWindowTitle(PLUGIN_NAME)
        self._is_pinned = False
        self._is_dirty = False
        self._suspend_dirty_tracking = False
        self._current_board_path = None
        self._settings = current_settings()
        self._icon_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources",
            "icons",
        )
        self._serializer = RefBoardSerializer()
        self._file_manager = FileManager()
        self._settings_dialog = None
        self._autosave_timer = QtCore.QTimer(self)
        self._autosave_timer.timeout.connect(self._autosave_if_needed)
        self._build_ui()
        self._apply_runtime_settings(self._settings)

    def _build_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = QtWidgets.QFrame(self)
        self.toolbar.setObjectName("RefBoardToolbarPlaceholder")
        self.toolbar.setFixedHeight(37)
        toolbar_layout = QtWidgets.QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)
        toolbar_layout.setSpacing(6)

        self.new_board_button = self._toolbar_button("New Board", "Create a new board")
        self.switch_board_button = self._toolbar_button("Switch Board", "Switch to another board")
        self.import_board_button = self._toolbar_button("Import Board", "Import an existing .refboard")
        self.save_board_button = self._toolbar_button("Save Board", "Save the current board")
        self.save_as_board_button = self._toolbar_button("Save As", "Save the current board as...")
        self.settings_button = self._toolbar_button("Settings", "RefBoard Settings")
        self.board_identifier_label = QtWidgets.QLabel(self.toolbar)
        self.board_identifier_label.setObjectName("RefBoardBoardIdentifierLabel")
        self.board_identifier_label.setAlignment(QtCore.Qt.AlignCenter)
        self.board_identifier_label.setFixedWidth(180)
        self.board_identifier_label.setText("")
        self.board_identifier_label.setProperty("hasIdentifier", False)
        self.pin_button = QtWidgets.QToolButton(self.toolbar)
        self.pin_button.setObjectName("RefBoardPinButton")
        self.pin_button.setToolTip("Keep panel on top")
        self.pin_button.setCheckable(True)
        self.pin_button.setAutoRaise(False)
        self.pin_button.setIconSize(QtCore.QSize(20, 20))
        self.pin_button.setFixedSize(QtCore.QSize(34, 30))
        self.pin_button.toggled.connect(self._set_window_pinned)
        self._update_pin_button_icon(False)
        self._set_toolbar_button_icon(self.new_board_button, "icon_NewBoard.svg")
        self._set_toolbar_button_icon(self.switch_board_button, "icon_SwitchBoard.svg")
        self._set_toolbar_button_icon(self.import_board_button, "icon_ImportBoard.svg")
        self._set_toolbar_button_icon(self.save_board_button, "icon_Save.svg")
        self._set_toolbar_button_icon(self.save_as_board_button, "icon_SaveAs.svg")
        self._set_toolbar_button_icon(self.settings_button, "icon_Setting.svg")

        toolbar_layout.addWidget(self.new_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.import_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.switch_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.save_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.save_as_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self._toolbar_separator(), 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.settings_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.board_identifier_label, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.pin_button, 0, QtCore.Qt.AlignVCenter)

        self.canvas = RefCanvasView(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)
        self.loading_overlay = RefBoardLoadingOverlay(self)
        self.save_toast = RefBoardSaveToast(self)
        self.canvas.boardChanged.connect(self._on_board_changed)
        self.new_board_button.clicked.connect(self._handle_new_board_clicked)
        self.import_board_button.clicked.connect(self._import_board)
        self.save_board_button.clicked.connect(self._save_board)
        self.save_as_board_button.clicked.connect(self._save_board_as)
        self.switch_board_button.clicked.connect(self._switch_board)
        self.settings_button.clicked.connect(self._open_settings_dialog)

    def _toolbar_button(self, text, tooltip):
        button = QtWidgets.QToolButton(self.toolbar)
        button.setObjectName("RefBoardToolbarButton")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setAutoRaise(False)
        button.setIconSize(QtCore.QSize(20, 20))
        button.setFixedSize(QtCore.QSize(58, 29))
        return button

    def _set_toolbar_button_icon(self, button, icon_name):
        icon_path = os.path.join(self._icon_dir, icon_name)
        if not os.path.exists(icon_path):
            return
        button.setIcon(QtGui.QIcon(icon_path))
        button.setText("")

    def _toolbar_separator(self):
        separator = QtWidgets.QFrame(self.toolbar)
        separator.setObjectName("RefBoardToolbarSeparator")
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Plain)
        separator.setFixedWidth(14)
        separator.setFixedHeight(18)
        return separator

    def _show_placeholder_message(self, title):
        QtWidgets.QMessageBox.information(
            self,
            title,
            "{0} is a placeholder for the upcoming board workflow.".format(title),
        )

    def _open_settings_dialog(self):
        if self._settings_dialog is None:
            self._settings_dialog = RefBoardSettingsDialog(self)
            self._settings_dialog.settingsApplied.connect(self._apply_settings)
        self._settings_dialog.load_settings(self._settings)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def open_settings_dialog(self):
        self._open_settings_dialog()

    def debug_mode_enabled(self):
        return bool(self._settings.get("debug_mode"))

    def _handle_new_board_clicked(self):
        if not self._confirm_safe_board_change("create a new board"):
            return
        if self._nuke_scene_requires_save():
            QtWidgets.QMessageBox.information(
                self,
                "Please Save Scene",
                "Please save the current Nuke scene first.",
            )
            return
        identifier = self._prompt_new_board_identifier()
        if identifier is None:
            return
        board_path = self._build_new_board_path(identifier)
        if not board_path:
            QtWidgets.QMessageBox.warning(
                self,
                "Create Board Failed",
                "RefBoard could not build a board path from the current scene.",
            )
            return
        if os.path.exists(board_path):
            reply = QtWidgets.QMessageBox.question(
                self,
                "Board Already Exists",
                "A board with this name already exists.\n\nOverwrite it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
        self._new_board(board_path)

    def _new_board(self, board_path=None):
        self._suspend_dirty_tracking = True
        self.canvas.clear_board()
        self._suspend_dirty_tracking = False
        self._current_board_path = None
        self._set_dirty(False)
        if board_path:
            self._save_board_to_path(board_path)

    def _import_board(self):
        if not self._confirm_safe_board_change("import another board"):
            return
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open RefBoard",
            "",
            "RefBoard Files (*{0})".format(FILE_EXTENSION),
        )
        if not file_path:
            return
        self._load_board_from_path(file_path)

    def _switch_board(self):
        if not self._confirm_safe_board_change("switch boards"):
            return
        scene_path = self._current_nuke_scene_path()
        if not scene_path:
            QtWidgets.QMessageBox.information(
                self,
                "Please Save Scene",
                "Please save the current Nuke scene first.",
            )
            return
        board_choices = self._scene_board_choices()
        if not board_choices:
            QtWidgets.QMessageBox.information(
                self,
                "No RefBoards Found",
                "No .refboard files were found next to the current scene.",
            )
            return

        labels = [choice[0] for choice in board_choices]
        selected_label, accepted = QtWidgets.QInputDialog.getItem(
            self,
            "Switch Board",
            "Choose a board from the current Nuke scene folder:",
            labels,
            0,
            False,
        )
        if not accepted or not selected_label:
            return

        for label, file_path in board_choices:
            if label == selected_label:
                self._load_board_from_path(file_path)
                return

    def _save_board(self):
        if not self._current_board_path:
            return self._save_board_as()
        return self._save_board_to_path(self._current_board_path)

    def _save_board_as(self):
        file_path = self._prompt_save_path()
        return self._save_board_to_path(file_path)

    def _save_board_to_path(self, file_path):
        if not file_path:
            return False
        try:
            self._serializer.save(
                file_path,
                self.canvas.board_model(),
                self.canvas.image_models(),
                self.canvas.note_models(),
                self.canvas.nodemark_models(),
                self.canvas.framejump_models(),
            )
        except Exception as exc:
            self.save_toast.show_error_bottom_left("RefBoard save failed")
            self._show_save_failure_message(exc)
            return False
        self._current_board_path = file_path
        self._set_dirty(False)
        self.save_toast.show_bottom_left("RefBoard saved")
        return True

    def _prompt_save_path(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save RefBoard",
            "",
            "RefBoard Files (*{0})".format(FILE_EXTENSION),
        )
        if not file_path:
            return None
        if not file_path.lower().endswith(FILE_EXTENSION):
            file_path += FILE_EXTENSION
        return file_path

    def _prompt_new_board_identifier(self):
        identifier, accepted = QtWidgets.QInputDialog.getText(
            self,
            "Create New Board",
            "Board identifier (saved next to the current Nuke scene):",
        )
        if not accepted:
            return None
        identifier = self._sanitize_board_identifier(identifier)
        if not identifier:
            QtWidgets.QMessageBox.information(
                self,
                "Identifier Required",
                "Please enter a valid board identifier.",
            )
            return None
        return identifier

    def _sanitize_board_identifier(self, identifier):
        text = (identifier or "").strip()
        text = re.sub(r"\s+", "_", text)
        text = re.sub(r'[<>:"/\\|?*]+', "_", text)
        text = re.sub(r"_+", "_", text).strip("._")
        return text

    def _build_new_board_path(self, identifier):
        scene_path = self._current_nuke_scene_path()
        if not scene_path:
            return None
        scene_dir = os.path.dirname(scene_path)
        scene_name = os.path.splitext(os.path.basename(scene_path))[0]
        file_name = "{0}_boardRef_{1}{2}".format(scene_name, identifier, FILE_EXTENSION)
        return os.path.join(scene_dir, file_name)

    def _load_board_from_path(self, file_path):
        extract_dir = self._file_manager.extraction_dir(file_path)
        self.loading_overlay.show_centered()
        QtWidgets.QApplication.processEvents()
        try:
            board_model, image_models, note_models, nodemark_models, framejump_models = self._serializer.load(
                file_path, extract_dir
            )
            self._suspend_dirty_tracking = True
            self.canvas.load_board(board_model, image_models, note_models, nodemark_models, framejump_models)
            self._suspend_dirty_tracking = False
            self._current_board_path = file_path
            self._set_dirty(False)
        except Exception as exc:
            self.save_toast.show_error_bottom_left("RefBoard load failed")
            self._show_load_failure_message(exc)
            return False
        finally:
            self._suspend_dirty_tracking = False
            self.loading_overlay.hide()
        return True

    def _set_window_pinned(self, pinned):
        self._is_pinned = bool(pinned)
        self._update_pin_button_icon(self._is_pinned)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, self._is_pinned)
        self.show()
        self.raise_()
        self.activateWindow()

    def _update_pin_button_icon(self, pinned):
        icon_name = "Pined.svg" if pinned else "Unpin.svg"
        icon_path = os.path.join(self._icon_dir, icon_name)
        if os.path.exists(icon_path):
            self.pin_button.setIcon(QtGui.QIcon(icon_path))
            self.pin_button.setText("")
        else:
            self.pin_button.setIcon(QtGui.QIcon())
            self.pin_button.setText("Pinned" if pinned else "Pin")

    def resizeEvent(self, event):
        super(RefBoardPanel, self).resizeEvent(event)
        if hasattr(self, "loading_overlay") and self.loading_overlay.isVisible():
            self.loading_overlay.show_centered()
        if hasattr(self, "save_toast") and self.save_toast.isVisible():
            self.save_toast.reposition_bottom_left()

    def closeEvent(self, event):
        if not self._is_dirty:
            self._cleanup_runtime_cache_if_needed()
            super(RefBoardPanel, self).closeEvent(event)
            return

        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowTitle("Unsaved Changes")
        message_box.setText("This board has unsaved changes.")
        message_box.setInformativeText("Save before closing?")
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        save_button = message_box.addButton("Save", QtWidgets.QMessageBox.AcceptRole)
        discard_button = message_box.addButton("Don't Save", QtWidgets.QMessageBox.DestructiveRole)
        cancel_button = message_box.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        message_box.setDefaultButton(save_button)
        message_box.exec_()

        clicked = message_box.clickedButton()
        if clicked == save_button:
            if self._save_board():
                self._cleanup_runtime_cache_if_needed()
                super(RefBoardPanel, self).closeEvent(event)
                event.accept()
            else:
                event.ignore()
            return
        if clicked == discard_button:
            self._cleanup_runtime_cache_if_needed()
            super(RefBoardPanel, self).closeEvent(event)
            event.accept()
            return
        if clicked == cancel_button:
            event.ignore()
            return
        event.ignore()

    def contextMenuEvent(self, event):
        if not self.debug_mode_enabled():
            return
        menu = QtWidgets.QMenu(self)
        debug_menu = menu.addMenu("Dev Debug Test")
        toggle_loading_action = debug_menu.addAction("Test Loading Overlay")
        hide_loading_action = debug_menu.addAction("Hide Loading Overlay")
        debug_menu.addSeparator()
        test_save_toast_action = debug_menu.addAction("Test Save Toast")
        test_save_error_toast_action = debug_menu.addAction("Test Save Failed Toast")
        hide_save_toast_action = debug_menu.addAction("Hide Save Toast")
        action = menu.exec_(event.globalPos())
        if action == toggle_loading_action:
            self.loading_overlay.show_centered()
        elif action == hide_loading_action:
            self.loading_overlay.hide()
        elif action == test_save_toast_action:
            self.save_toast.show_bottom_left("RefBoard saved")
        elif action == test_save_error_toast_action:
            self.save_toast.show_error_bottom_left("RefBoard save failed")
        elif action == hide_save_toast_action:
            self.save_toast.hide()

    def _on_board_changed(self):
        if self._suspend_dirty_tracking:
            return
        self._set_dirty(True)

    def _set_dirty(self, dirty):
        self._is_dirty = bool(dirty)
        title = PLUGIN_NAME
        if self._current_board_path:
            title = "{0} - {1}".format(PLUGIN_NAME, os.path.basename(self._current_board_path))
        if self._is_dirty:
            title += " *"
        self.setWindowTitle(title)
        self._update_board_identifier_display()
        self.canvas.viewport().update()

    def set_max_undo_steps(self, steps):
        return self.canvas.set_max_undo_steps(steps)

    def max_undo_steps(self):
        return self.canvas.max_undo_steps()

    def _show_save_failure_message(self, exc):
        message = str(exc).strip() or exc.__class__.__name__
        QtWidgets.QMessageBox.warning(
            self,
            "Save Failed",
            "RefBoard could not be saved.\n\n{0}".format(message),
        )

    def _show_load_failure_message(self, exc):
        message = str(exc).strip() or exc.__class__.__name__
        QtWidgets.QMessageBox.warning(
            self,
            "Load Failed",
            "RefBoard could not be loaded.\n\n{0}".format(message),
        )

    def empty_state_message(self):
        if self._nuke_scene_requires_save():
            return u"Please save the Nuke scene first"
        if not self._current_board_path:
            return u"Create a board, switch board, or import a .refboard"
        return u">>>  Please drag the image here  <<<"

    def _apply_settings(self, settings):
        self._settings = update_settings(settings)
        self._apply_runtime_settings(self._settings)

    def _apply_runtime_settings(self, settings):
        settings = settings or {}
        custom_cache_enabled = bool(settings.get("use_custom_cache_directory"))
        configured_cache_dir = (settings.get("cache_directory") or "").strip()
        runtime_root = configured_cache_dir if custom_cache_enabled and configured_cache_dir else None
        FileManager.configure_runtime_root(runtime_root)
        self._file_manager.set_runtime_root(runtime_root)
        self.canvas.file_manager.set_runtime_root(runtime_root)
        self.canvas.apply_settings(settings)
        self.canvas.set_max_undo_steps(settings.get("max_undo_steps", 50))
        self._update_autosave_timer()
        self.resize(
            int(settings.get("default_panel_width", self.width()) or self.width()),
            int(settings.get("default_panel_height", self.height()) or self.height()),
        )

    def _update_autosave_timer(self):
        enabled = bool(self._settings.get("autosave_enabled"))
        interval_minutes = max(1, int(self._settings.get("autosave_interval_minutes", 10) or 10))
        if not enabled:
            self._autosave_timer.stop()
            return
        self._autosave_timer.start(interval_minutes * 60 * 1000)

    def _autosave_if_needed(self):
        if not self._settings.get("autosave_enabled"):
            return
        if not self._is_dirty or not self._current_board_path:
            return
        self._save_board_to_path(self._current_board_path)

    def _cleanup_runtime_cache_if_needed(self):
        if not self._settings.get("clean_cache_on_exit", True):
            return
        try:
            self._file_manager.clear_runtime_dir()
        except Exception:
            pass

    def _confirm_safe_board_change(self, action_label="continue"):
        if not self._is_dirty:
            return True
        QtWidgets.QMessageBox.information(
            self,
            "Unsaved Board",
            "Please save the current board before you {0}.".format(action_label),
        )
        return False

    def _nuke_scene_requires_save(self):
        return not bool(self._current_nuke_scene_path())

    def _current_nuke_scene_path(self):
        if nuke is None:
            return None
        try:
            root = nuke.root()
            if root is None:
                return None
            scene_path = root.name() or ""
            if scene_path == "Root":
                return None
            return scene_path
        except Exception:
            return None

    def _current_scene_base_name(self):
        scene_path = self._current_nuke_scene_path()
        if not scene_path:
            return None
        return os.path.splitext(os.path.basename(scene_path))[0]

    def _scene_board_choices(self):
        scene_path = self._current_nuke_scene_path()
        if not scene_path:
            return []
        scene_dir = os.path.dirname(scene_path)
        board_paths = []
        for name in sorted(os.listdir(scene_dir)):
            if not name.lower().endswith(FILE_EXTENSION):
                continue
            board_paths.append(os.path.join(scene_dir, name))

        used_labels = set()
        choices = []
        for board_path in board_paths:
            label = self._switch_board_label_for_path(board_path)
            unique_label = label
            suffix = 2
            while unique_label in used_labels:
                unique_label = "{0} ({1})".format(label, suffix)
                suffix += 1
            used_labels.add(unique_label)
            choices.append((unique_label, board_path))
        return choices

    def _switch_board_label_for_path(self, file_path):
        identifier = self._board_identifier_for_path(file_path)
        file_name = os.path.basename(file_path)
        if identifier:
            return "{0} - {1}".format(identifier, file_name)
        return os.path.splitext(file_name)[0]

    def _board_identifier_for_path(self, file_path):
        if not file_path:
            return ""
        scene_base_name = self._current_scene_base_name()
        if not scene_base_name:
            return ""
        file_name = os.path.basename(file_path)
        pattern = r"^{0}_boardRef_(.+){1}$".format(
            re.escape(scene_base_name),
            re.escape(FILE_EXTENSION),
        )
        match = re.match(pattern, file_name, re.IGNORECASE)
        if not match:
            return ""
        return match.group(1)

    def _update_board_identifier_display(self):
        identifier = self._board_identifier_for_path(self._current_board_path)
        has_identifier = bool(identifier)
        self.board_identifier_label.setProperty("hasIdentifier", has_identifier)
        self.board_identifier_label.setText(identifier if has_identifier else "=No Identifier =")
        self.board_identifier_label.style().unpolish(self.board_identifier_label)
        self.board_identifier_label.style().polish(self.board_identifier_label)
        self.board_identifier_label.update()
