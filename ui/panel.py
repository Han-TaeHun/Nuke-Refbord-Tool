# 主界面控制器 / Main dockable reference board panel controller.
import os

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

from refboard_core.constants import FILE_EXTENSION, PLUGIN_NAME
from refboard_core.file_manager import FileManager
from refboard_core.serializer import RefBoardSerializer
from ui.canvas_view import RefCanvasView
from ui.status_overlay import RefBoardLoadingOverlay, RefBoardSaveToast
from ui.styles import PANEL_STYLE


class RefBoardPanel(QtWidgets.QWidget):
    """Floating Nuke RefBoard panel with the first interactive canvas."""

    def __init__(self, parent=None):
        super(RefBoardPanel, self).__init__(parent)
        self.setObjectName("NukeRefBoardPanel")
        self.setWindowTitle(PLUGIN_NAME)
        self._is_pinned = False
        self._current_board_path = None
        self._icon_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources",
            "icons",
        )
        self._serializer = RefBoardSerializer()
        self._file_manager = FileManager()
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = QtWidgets.QFrame(self)
        self.toolbar.setObjectName("RefBoardToolbarPlaceholder")
        self.toolbar.setFixedHeight(32)
        toolbar_layout = QtWidgets.QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(8, 3, 8, 3)
        toolbar_layout.setSpacing(6)

        self.new_board_button = self._toolbar_button("New Canvas", "Create new board")
        self.switch_board_button = self._toolbar_button("Switch Canvas", "Switch board")
        self.import_board_button = self._toolbar_button("Import Canvas", "Import existing .refboard")
        self.save_board_button = self._toolbar_button("Save Canvas", "Save board")
        self.auto_load_board_button = self._toolbar_button(
            "Auto Load Canvas",
            "Automatically load a board canvas for the current script",
        )
        self.settings_button = self._toolbar_button("Settings", "RefBoard Settings")
        self.pin_button = QtWidgets.QToolButton(self.toolbar)
        self.pin_button.setObjectName("RefBoardPinButton")
        self.pin_button.setToolTip("Keep panel on top")
        self.pin_button.setCheckable(True)
        self.pin_button.setAutoRaise(False)
        self.pin_button.setIconSize(QtCore.QSize(16, 16))
        self.pin_button.toggled.connect(self._set_window_pinned)
        self._update_pin_button_icon(False)
        self._set_toolbar_button_icon(self.new_board_button, "icon_NewBoard.svg")
        self._set_toolbar_button_icon(self.switch_board_button, "icon_SwitchBoard.svg")
        self._set_toolbar_button_icon(self.import_board_button, "icon_ImportBoard.svg")
        self._set_toolbar_button_icon(self.save_board_button, "icon_Save.svg")
        self._set_toolbar_button_icon(self.auto_load_board_button, "icon_autoload.svg")
        self._set_toolbar_button_icon(self.settings_button, "icon_Setting.svg")

        toolbar_layout.addWidget(self.new_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.import_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.switch_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.save_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self._toolbar_separator(), 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.auto_load_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.settings_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.pin_button, 0, QtCore.Qt.AlignVCenter)

        self.canvas = RefCanvasView(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)
        self.loading_overlay = RefBoardLoadingOverlay(self)
        self.save_toast = RefBoardSaveToast(self)
        self.new_board_button.clicked.connect(self._new_board)
        self.import_board_button.clicked.connect(self._import_board)
        self.save_board_button.clicked.connect(self._save_board)
        self.switch_board_button.clicked.connect(lambda: self._show_placeholder_message("Switch Canvas"))
        self.auto_load_board_button.clicked.connect(lambda: self._show_placeholder_message("Auto Load Canvas"))
        self.settings_button.clicked.connect(lambda: self._show_placeholder_message("Settings"))

    def _toolbar_button(self, text, tooltip):
        button = QtWidgets.QToolButton(self.toolbar)
        button.setObjectName("RefBoardToolbarButton")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setAutoRaise(False)
        button.setIconSize(QtCore.QSize(16, 16))
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

    def _new_board(self):
        self.canvas.clear_board()
        self._current_board_path = None
        self.setWindowTitle(PLUGIN_NAME)

    def _import_board(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open RefBoard",
            "",
            "RefBoard Files (*{0})".format(FILE_EXTENSION),
        )
        if not file_path:
            return
        self._load_board_from_path(file_path)

    def _save_board(self):
        file_path = self._current_board_path or self._prompt_save_path()
        if not file_path:
            return
        self._serializer.save(
            file_path,
            self.canvas.board_model(),
            self.canvas.image_models(),
            self.canvas.note_models(),
            self.canvas.nodemark_models(),
        )
        self._current_board_path = file_path
        self.setWindowTitle("{0} - {1}".format(PLUGIN_NAME, os.path.basename(file_path)))
        self.save_toast.show_bottom_left("RefBoard saved")

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

    def _load_board_from_path(self, file_path):
        extract_dir = self._file_manager.extraction_dir(file_path)
        self.loading_overlay.show_centered()
        QtWidgets.QApplication.processEvents()
        try:
            board_model, image_models, note_models, nodemark_models = self._serializer.load(file_path, extract_dir)
            self.canvas.load_board(board_model, image_models, note_models, nodemark_models)
            self._current_board_path = file_path
            self.setWindowTitle("{0} - {1}".format(PLUGIN_NAME, os.path.basename(file_path)))
        finally:
            self.loading_overlay.hide()

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
            self.save_toast.show_bottom_left(self.save_toast.body_label.text(), 2200)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        toggle_loading_action = menu.addAction("Test Loading Overlay")
        hide_loading_action = menu.addAction("Hide Loading Overlay")
        menu.addSeparator()
        test_save_toast_action = menu.addAction("Test Save Toast")
        hide_save_toast_action = menu.addAction("Hide Save Toast")
        action = menu.exec_(event.globalPos())
        if action == toggle_loading_action:
            self.loading_overlay.show_centered()
        elif action == hide_loading_action:
            self.loading_overlay.hide()
        elif action == test_save_toast_action:
            self.save_toast.show_bottom_left("RefBoard saved")
        elif action == hide_save_toast_action:
            self.save_toast.hide()
