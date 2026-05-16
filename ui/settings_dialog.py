# 设置界面对话框 / Preferences-style settings dialog.
try:
    from PySide2 import QtCore, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtWidgets

from ui.styles import PANEL_STYLE


class RefBoardSettingsDialog(QtWidgets.QDialog):
    """Preferences-style placeholder settings dialog for future board options."""

    def __init__(self, parent=None):
        super(RefBoardSettingsDialog, self).__init__(parent)
        self.setObjectName("RefBoardSettingsDialog")
        self.setWindowTitle("Preferences - General")
        self.setModal(True)
        self.resize(1160, 820)
        self.setStyleSheet(PANEL_STYLE)
        self._build_ui()
        self._populate_categories()
        self._left_tree.expandAll()
        self._left_tree.setCurrentItem(self._left_tree.topLevelItem(0))

    def _build_ui(self):
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        self._content_frame = QtWidgets.QFrame(self)
        self._content_frame.setObjectName("RefBoardSettingsFrame")
        content_layout = QtWidgets.QHBoxLayout(self._content_frame)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(16)

        self._left_panel = QtWidgets.QFrame(self._content_frame)
        self._left_panel.setObjectName("RefBoardSettingsNavPanel")
        left_layout = QtWidgets.QVBoxLayout(self._left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        self._left_tree = QtWidgets.QTreeWidget(self._left_panel)
        self._left_tree.setObjectName("RefBoardSettingsTree")
        self._left_tree.setHeaderHidden(True)
        self._left_tree.setIndentation(14)
        self._left_tree.currentItemChanged.connect(self._on_category_changed)
        left_layout.addWidget(self._left_tree, 1)

        self._right_panel = QtWidgets.QFrame(self._content_frame)
        self._right_panel.setObjectName("RefBoardSettingsPagePanel")
        right_layout = QtWidgets.QVBoxLayout(self._right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        self._page_title = QtWidgets.QLabel("General", self._right_panel)
        self._page_title.setObjectName("RefBoardSettingsPageTitle")
        right_layout.addWidget(self._page_title)

        self._stack = QtWidgets.QStackedWidget(self._right_panel)
        self._stack.setObjectName("RefBoardSettingsStack")
        right_layout.addWidget(self._stack, 1)

        content_layout.addWidget(self._left_panel, 0)
        content_layout.addWidget(self._right_panel, 1)
        root_layout.addWidget(self._content_frame, 1)

        footer_layout = QtWidgets.QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.addStretch(1)

        self._save_button = QtWidgets.QPushButton("Save", self)
        self._apply_button = QtWidgets.QPushButton("Apply", self)
        self._cancel_button = QtWidgets.QPushButton("Cancel", self)
        self._save_button.clicked.connect(self.accept)
        self._apply_button.clicked.connect(self._apply_placeholder)
        self._cancel_button.clicked.connect(self.reject)
        footer_layout.addWidget(self._save_button)
        footer_layout.addWidget(self._apply_button)
        footer_layout.addWidget(self._cancel_button)
        root_layout.addLayout(footer_layout)

    def _populate_categories(self):
        pages = [
            ("General", None, self._build_general_page()),
            ("Canvas", None, self._build_canvas_page()),
            ("Autosave", None, self._build_autosave_page()),
            ("Paths", None, self._build_paths_page()),
            ("NodeMark", None, self._build_nodemark_page()),
            ("Performance", None, self._build_performance_page()),
            ("About", None, self._build_about_page()),
        ]

        for title, parent_title, widget in pages:
            item = QtWidgets.QTreeWidgetItem([title])
            item.setData(0, QtCore.Qt.UserRole, self._stack.addWidget(widget))
            if parent_title is None:
                self._left_tree.addTopLevelItem(item)
            else:
                parent_item = self._find_or_create_group(parent_title)
                parent_item.addChild(item)

        advanced_group = self._find_or_create_group("Advanced")
        for title, widget in [
            ("Experimental", self._build_experimental_page()),
            ("Debug", self._build_debug_page()),
        ]:
            item = QtWidgets.QTreeWidgetItem([title])
            item.setData(0, QtCore.Qt.UserRole, self._stack.addWidget(widget))
            advanced_group.addChild(item)

    def _find_or_create_group(self, title):
        for index in range(self._left_tree.topLevelItemCount()):
            item = self._left_tree.topLevelItem(index)
            if item.text(0) == title:
                return item
        group = QtWidgets.QTreeWidgetItem([title])
        group.setFlags(group.flags() & ~QtCore.Qt.ItemIsSelectable)
        self._left_tree.addTopLevelItem(group)
        return group

    def _on_category_changed(self, current, previous):
        del previous
        if current is None:
            return
        page_index = current.data(0, QtCore.Qt.UserRole)
        if page_index is None:
            return
        self._page_title.setText(current.text(0))
        self.setWindowTitle("Preferences - {0}".format(current.text(0)))
        self._stack.setCurrentIndex(int(page_index))

    def _build_general_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._section_title("Workspace"))
        layout.addWidget(self._kv_row("Current mode", self._line_edit("Single canvas placeholder")))
        layout.addWidget(self._kv_row("Theme", self._combo(["Dark", "Studio Gray", "Placeholder"])))
        layout.addWidget(self._kv_row("Startup behavior", self._combo(["Open last board", "Start empty", "Ask every time"])))
        layout.addSpacing(10)
        layout.addWidget(self._section_title("Quick Notes"))
        layout.addWidget(self._placeholder_box("General settings placeholder area.\nLater we can place board name rules, startup defaults, and UI behavior here."))
        layout.addStretch(1)
        return page

    def _build_canvas_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._section_title("Canvas Defaults"))
        layout.addWidget(self._kv_row("Default zoom step", self._spin_box(15, suffix="%")))
        layout.addWidget(self._kv_row("Default note size", self._spin_box(18, suffix=" pt")))
        layout.addWidget(self._kv_row("Maximum undo steps", self._spin_box(50)))
        layout.addSpacing(10)
        layout.addWidget(self._section_title("Placeholders"))
        layout.addWidget(self._placeholder_box("Canvas-related settings placeholder.\nThis is where note defaults, background look, and interaction options can live later."))
        layout.addStretch(1)
        return page

    def _build_autosave_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._section_title("Autosave"))
        layout.addWidget(self._kv_row("Enable autosave", self._checkbox("Placeholder toggle", True)))
        layout.addWidget(self._kv_row("Idle autosave after", self._spin_box(8, suffix=" sec")))
        layout.addWidget(self._kv_row("Force autosave after", self._spin_box(30, suffix=" sec")))
        layout.addWidget(self._kv_row("Autosave filename", self._line_edit("board_name.autosave.refboard")))
        layout.addStretch(1)
        return page

    def _build_paths_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._section_title("Runtime Paths"))
        layout.addWidget(self._kv_row("Temp directory", self._line_edit("F:/R_D/NukeRefBoard/temp")))
        layout.addWidget(self._kv_row("Imported board cache", self._line_edit("temp/<board_name>")))
        layout.addSpacing(10)
        layout.addWidget(self._section_title("Path Table Placeholder"))
        table = QtWidgets.QTableWidget(4, 3, page)
        table.setObjectName("RefBoardSettingsTable")
        table.setHorizontalHeaderLabels(["Windows", "macOS", "Linux"])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        for row in range(4):
            for col in range(3):
                table.setItem(row, col, QtWidgets.QTableWidgetItem("Placeholder"))
        layout.addWidget(table, 1)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self._mini_button("+"))
        buttons.addWidget(self._mini_button("-"))
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return page

    def _build_nodemark_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._section_title("NodeMark"))
        layout.addWidget(self._kv_row("Backdrop prefix", self._line_edit("RefBoardToolsetBackdrop_")))
        layout.addWidget(self._kv_row("Auto label style", self._combo(["Label slug", "Original label", "Custom later"])))
        layout.addWidget(self._kv_row("Missing NodeMark behavior", self._combo(["Show warning", "Silent fail", "Try fallback"])))
        layout.addStretch(1)
        return page

    def _build_performance_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._section_title("Performance"))
        layout.addWidget(self._kv_row("Thumbnail cache", self._checkbox("Use placeholder cache", True)))
        layout.addWidget(self._kv_row("Image import mode", self._combo(["Balanced", "Fast", "Quality first"])))
        layout.addWidget(self._kv_row("Large board behavior", self._combo(["Normal", "Lazy load later", "Placeholder"])))
        layout.addStretch(1)
        return page

    def _build_about_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._section_title("About Nuke RefBoard"))
        layout.addWidget(self._placeholder_box("Preferences dialog placeholder.\nThis page can later show version info, storage format version, and support links."))
        layout.addStretch(1)
        return page

    def _build_experimental_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._section_title("Experimental"))
        layout.addWidget(self._checkbox("Enable placeholder future feature A", False))
        layout.addWidget(self._checkbox("Enable placeholder future feature B", False))
        layout.addStretch(1)
        return page

    def _build_debug_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._section_title("Debug"))
        layout.addWidget(self._checkbox("Show verbose logs placeholder", False))
        layout.addWidget(self._checkbox("Enable save-failure test hooks placeholder", True))
        layout.addWidget(self._placeholder_box("Future debug switches and developer-only settings can live here."))
        layout.addStretch(1)
        return page

    def _page_container(self):
        page = QtWidgets.QWidget(self._stack)
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        return page

    def _section_title(self, text):
        label = QtWidgets.QLabel(text, self)
        label.setObjectName("RefBoardSettingsSectionTitle")
        return label

    def _kv_row(self, label_text, widget):
        row = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        label = QtWidgets.QLabel(label_text, row)
        label.setObjectName("RefBoardSettingsFieldLabel")
        label.setMinimumWidth(180)
        layout.addWidget(label, 0)
        layout.addWidget(widget, 1)
        return row

    def _line_edit(self, text):
        widget = QtWidgets.QLineEdit(text, self)
        widget.setObjectName("RefBoardSettingsLineEdit")
        return widget

    def _combo(self, items):
        widget = QtWidgets.QComboBox(self)
        widget.setObjectName("RefBoardSettingsCombo")
        widget.addItems(items)
        return widget

    def _spin_box(self, value, suffix=""):
        widget = QtWidgets.QSpinBox(self)
        widget.setObjectName("RefBoardSettingsSpinBox")
        widget.setRange(0, 9999)
        widget.setValue(int(value))
        if suffix:
            widget.setSuffix(suffix)
        return widget

    def _checkbox(self, text, checked):
        widget = QtWidgets.QCheckBox(text, self)
        widget.setChecked(bool(checked))
        widget.setObjectName("RefBoardSettingsCheckBox")
        return widget

    def _placeholder_box(self, text):
        box = QtWidgets.QFrame(self)
        box.setObjectName("RefBoardSettingsPlaceholderBox")
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(14, 12, 14, 12)
        label = QtWidgets.QLabel(text, box)
        label.setWordWrap(True)
        label.setObjectName("RefBoardSettingsPlaceholderText")
        layout.addWidget(label)
        return box

    def _mini_button(self, text):
        button = QtWidgets.QPushButton(text, self)
        button.setObjectName("RefBoardSettingsMiniButton")
        button.setFixedSize(30, 30)
        return button

    def _apply_placeholder(self):
        QtWidgets.QToolTip.showText(
            self.mapToGlobal(QtCore.QPoint(self.width() - 150, self.height() - 44)),
            "Apply placeholder",
            self,
        )
