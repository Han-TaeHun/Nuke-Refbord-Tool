# 主界面控制器 / Main dockable reference board panel controller.
try:
    from PySide2 import QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtWidgets

from refboard_core.constants import PLUGIN_NAME
from ui.canvas_view import RefCanvasView
from ui.styles import PANEL_STYLE


class RefBoardPanel(QtWidgets.QWidget):
    """Floating Nuke RefBoard panel with the first interactive canvas."""

    def __init__(self, parent=None):
        super(RefBoardPanel, self).__init__(parent)
        self.setObjectName("NukeRefBoardPanel")
        self.setWindowTitle(PLUGIN_NAME)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.canvas = RefCanvasView(self)
        layout.addWidget(self.canvas, 1)
