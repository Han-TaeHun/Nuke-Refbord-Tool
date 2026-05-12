# 顶部工具栏组件 / Top toolbar component for board actions.
try:
    from PySide2 import QtCore, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtWidgets


class RefBoardToolbar(QtWidgets.QToolBar):
    """Top toolbar for board file actions."""

    openRequested = QtCore.Signal()
    saveRequested = QtCore.Signal()
    clearRequested = QtCore.Signal()
    addImageRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super(RefBoardToolbar, self).__init__(parent)
        self.setMovable(False)
        self.setIconSize(QtCore.QSize(16, 16))
        self._add_actions()

    def _add_actions(self):
        self.addAction("Open", self.openRequested.emit)
        self.addAction("Save", self.saveRequested.emit)
        self.addSeparator()
        self.addAction("Add Image", self.addImageRequested.emit)
        self.addAction("Clear", self.clearRequested.emit)
