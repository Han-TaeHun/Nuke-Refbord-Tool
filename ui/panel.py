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

        self.pin_button = QtWidgets.QToolButton(self.toolbar)
        self.pin_button.setObjectName("RefBoardPinButton")
        self.pin_button.setToolTip("Keep this panel on top during the current Nuke session")
        self.pin_button.setCheckable(True)
        self.pin_button.setAutoRaise(False)
        self.pin_button.setIconSize(QtCore.QSize(16, 16))
        self.pin_button.toggled.connect(self._set_window_pinned)
        self._update_pin_button_icon(False)

        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.pin_button, 0, QtCore.Qt.AlignVCenter)

        self.canvas = RefCanvasView(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)

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
