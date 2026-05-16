# 状态提示浮层 / Status overlay widgets.
try:
    from PySide2 import QtCore, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtWidgets


class RefBoardLoadingOverlay(QtWidgets.QFrame):
    """Frameless centered loading placeholder overlay for the RefBoard panel."""

    def __init__(self, parent=None):
        super(RefBoardLoadingOverlay, self).__init__(parent)
        self.setObjectName("RefBoardLoadingOverlay")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.hide()
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)

        self.title_label = QtWidgets.QLabel("Loading RefBoard...", self)
        self.title_label.setObjectName("RefBoardLoadingTitle")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)

        self.body_label = QtWidgets.QLabel("Please Wait", self)
        self.body_label.setObjectName("RefBoardLoadingBody")
        self.body_label.setAlignment(QtCore.Qt.AlignCenter)
        self.body_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.body_label)

    def show_centered(self):
        if self.parentWidget() is None:
            self.show()
            return
        self.adjustSize()
        parent_rect = self.parentWidget().rect()
        x = int((parent_rect.width() - self.width()) * 0.5)
        y = int((parent_rect.height() - self.height()) * 0.5)
        self.move(max(0, x), max(0, y))
        self.show()
        self.raise_()


class RefBoardSaveToast(QtWidgets.QFrame):
    """Small bottom-left toast placeholder for save feedback."""

    def __init__(self, parent=None):
        super(RefBoardSaveToast, self).__init__(parent)
        self.setObjectName("RefBoardSaveToast")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.hide()
        self._hide_timer = QtCore.QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        self.body_label = QtWidgets.QLabel("RefBoard saved", self)
        self.body_label.setObjectName("RefBoardSaveToastText")
        self.body_label.setAlignment(QtCore.Qt.AlignCenter)

        layout.addWidget(self.body_label)

    def show_bottom_left(self, text="RefBoard saved", duration_ms=2200):
        self.body_label.setText(text)
        if self.parentWidget() is None:
            self.show()
            return
        self.adjustSize()
        parent_rect = self.parentWidget().rect()
        x = 18
        y = max(0, parent_rect.height() - self.height() - 18)
        self.move(x, y)
        self.show()
        self.raise_()
        self._hide_timer.start(max(400, int(duration_ms)))
