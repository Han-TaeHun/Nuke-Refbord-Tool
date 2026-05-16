# 主界面控制器 / Main dockable reference board panel controller.
import os

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

from refboard_core.constants import PLUGIN_NAME
from ui.canvas_view import RefCanvasView
from ui.styles import PANEL_STYLE


class RefBoardPanel(QtWidgets.QWidget):
    """Floating Nuke RefBoard panel with the first interactive canvas."""

    def __init__(self, parent=None):
        super(RefBoardPanel, self).__init__(parent)
        self.setObjectName("NukeRefBoardPanel")
        self.setWindowTitle(PLUGIN_NAME)
        self._is_pinned = False
        self._icon_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources",
            "icons",
        )
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

    def _toolbar_button(self, text, tooltip):
        button = QtWidgets.QToolButton(self.toolbar)
        button.setObjectName("RefBoardToolbarButton")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setAutoRaise(False)
        button.setIconSize(QtCore.QSize(16, 16))
        button.clicked.connect(lambda: self._show_placeholder_message(text))
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
