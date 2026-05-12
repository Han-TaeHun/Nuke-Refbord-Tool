# 主界面控制器 / Main dockable reference board panel controller.
try:
    from PySide2 import QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtWidgets

from refboard_core.constants import PLUGIN_NAME
from ui.styles import PANEL_STYLE


class RefBoardPanel(QtWidgets.QWidget):
    """Blank dockable panel for the first Nuke RefBoard milestone."""

    def __init__(self, parent=None):
        super(RefBoardPanel, self).__init__(parent)
        self.setObjectName("NukeRefBoardPanel")
        self.setWindowTitle(PLUGIN_NAME)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        placeholder = QtWidgets.QWidget(self)
        placeholder.setObjectName("RefBoardBlankPanel")
        layout.addWidget(placeholder, 1)
