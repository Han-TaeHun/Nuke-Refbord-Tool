# NodeMark 선택 다이얼로그
try:
    from PySide2 import QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtWidgets


class AddNodeMarkDialog(QtWidgets.QDialog):
    """Dialog for selecting a NodeMark and optionally renaming its link label."""

    def __init__(self, nodemarks, parent=None):
        super().__init__(parent)
        self._nodemarks = list(nodemarks or [])
        self.setWindowTitle("Add NodeMark")
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        choose_label = QtWidgets.QLabel("Choose a NodeMark:", self)
        layout.addWidget(choose_label)

        self.combo_box = QtWidgets.QComboBox(self)
        for item in self._nodemarks:
            self.combo_box.addItem(item["display_label"], item)
        layout.addWidget(self.combo_box)

        rename_label = QtWidgets.QLabel("Rename as (optional):", self)
        layout.addWidget(rename_label)

        self.rename_edit = QtWidgets.QLineEdit(self)
        self.rename_edit.setPlaceholderText("Optional")
        layout.addWidget(self.rename_edit)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            parent=self,
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def selected_nodemark(self):
        index = self.combo_box.currentIndex()
        return self.combo_box.itemData(index)

    def display_label(self):
        return self.rename_edit.text().strip()
