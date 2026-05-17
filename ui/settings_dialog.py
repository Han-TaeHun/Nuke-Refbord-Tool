# 设置界面对话框 / Preferences-style settings dialog.
try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

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
        self._reset_button = QtWidgets.QPushButton("Reset", self)
        self._reset_button.clicked.connect(self._reset_placeholder)
        footer_layout.addWidget(self._reset_button)
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
            ("Autosave", None, self._build_autosave_page()),
            ("Paths / Storage", None, self._build_storage_page()),
            ("Canvas", None, self._build_canvas_page()),
            ("Text / Notes", None, self._build_text_notes_page()),
            ("NodeMark", None, self._build_nodemark_page()),
        ]

        for title, parent_title, widget in pages:
            item = QtWidgets.QTreeWidgetItem([title])
            item.setData(0, QtCore.Qt.UserRole, self._stack.addWidget(widget))
            if parent_title is None:
                self._left_tree.addTopLevelItem(item)
            else:
                parent_item = self._find_or_create_group(parent_title)
                parent_item.addChild(item)

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

    def _build_autosave_page(self):
        page = self._page_container()
        layout = page.layout()
        self._autosave_enable_checkbox = self._checkbox_only(True)
        self._autosave_force_spinbox = self._spin_box(10, suffix=" min")

        layout.addWidget(self._kv_row("Enable autosave", self._autosave_enable_checkbox))
        layout.addWidget(self._kv_row("Autosave interval", self._autosave_force_spinbox))
        layout.addSpacing(10)
        layout.addWidget(
            self._placeholder_box(
                "This page is reserved for autosave behavior only.\n"
                "The real save timer, idle detection, and forced interval logic can be connected later."
            )
        )
        self._autosave_enable_checkbox.toggled.connect(self._update_autosave_controls_state)
        self._update_autosave_controls_state(self._autosave_enable_checkbox.isChecked())
        layout.addStretch(1)
        return page

    def _build_storage_page(self):
        page = self._page_container()
        layout = page.layout()
        self._custom_cache_checkbox = self._checkbox_only(False)
        self._cache_path_picker = self._path_picker("Choose cache directory...", "Select Folder")
        self._clean_cache_checkbox = self._checkbox_only(True)

        layout.addWidget(self._kv_row("Use custom cache directory", self._custom_cache_checkbox))
        layout.addWidget(self._kv_row("Cache directory", self._cache_path_picker))
        layout.addWidget(self._kv_row("Clean cache on exit", self._clean_cache_checkbox))
        layout.addSpacing(10)
        layout.addWidget(
            self._placeholder_box(
                "This page will later manage runtime storage, extracted .refboard assets, "
                "and any custom temp folder chosen from the settings window."
            )
        )
        self._custom_cache_checkbox.toggled.connect(self._update_cache_path_controls_state)
        self._update_cache_path_controls_state(self._custom_cache_checkbox.isChecked())
        layout.addStretch(1)
        return page

    def _build_canvas_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._kv_row("Maximum undo steps", self._spin_box(50)))
        layout.addWidget(self._kv_row("Default panel width", self._spin_box(1280, suffix=" px")))
        layout.addWidget(self._kv_row("Default panel height", self._spin_box(720, suffix=" px")))
        layout.addSpacing(10)
        layout.addWidget(
            self._placeholder_box(
                "Canvas settings placeholder.\n"
                "This page can later control startup canvas behavior, stacking rules, and window defaults."
            )
        )
        layout.addStretch(1)
        return page

    def _build_text_notes_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(self._kv_row("Default font", self._combo(["Verdana", "Arial", "Microsoft YaHei", "Placeholder"])))
        layout.addWidget(self._kv_row("Default font size", self._spin_box(18, suffix=" pt")))
        layout.addWidget(self._kv_row("Default text color", self._color_picker("#f2f2f2")))
        layout.addWidget(self._kv_row("Default text background", self._color_picker("#202124")))
        layout.addWidget(self._kv_row("Default transparent background", self._checkbox_only(False)))
        layout.addWidget(self._kv_row("Auto-enter edit mode for new text", self._checkbox_only(True)))
        layout.addWidget(self._kv_row("Continue checklist on new line", self._checkbox_only(True)))
        layout.addSpacing(10)
        layout.addWidget(
            self._placeholder_box(
                "Text and note defaults placeholder.\n"
                "This page is prepared for note style, checklist behavior, and new-text interaction defaults."
            )
        )
        layout.addStretch(1)
        return page

    def _build_nodemark_page(self):
        page = self._page_container()
        layout = page.layout()
        layout.addWidget(
            self._kv_row(
                "Default NodeMark link style",
                self._combo(["Hyperlink text", "Pill button"]),
            )
        )
        layout.addWidget(
            self._kv_row(
                "Missing backdrop behavior",
                self._combo(["Show warning", "Do nothing"]),
            )
        )
        layout.addWidget(self._kv_row("Default backdrop color", self._color_picker("#2F4F6F")))
        layout.addSpacing(10)
        layout.addWidget(
            self._placeholder_box(
                "NodeMark settings placeholder.\n"
                "This page is ready for jump-link behavior, target fallback rules, and default backdrop appearance."
            )
        )
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

    def _path_picker(self, text, button_text):
        row = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        line_edit = self._line_edit(text)
        browse_button = QtWidgets.QPushButton(button_text, row)
        browse_button.setObjectName("RefBoardSettingsBrowseButton")
        browse_button.setFixedHeight(28)
        browse_button.clicked.connect(lambda: self._pick_directory(line_edit))

        row._path_line_edit = line_edit
        row._browse_button = browse_button

        layout.addWidget(line_edit, 1)
        layout.addWidget(browse_button, 0)
        return row

    def _color_picker(self, color_value):
        row = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        swatch = QtWidgets.QPushButton(row)
        swatch.setObjectName("RefBoardSettingsColorSwatch")
        swatch.setFixedSize(30, 26)
        swatch.setCursor(QtCore.Qt.PointingHandCursor)

        line_edit = self._line_edit(color_value)
        line_edit.hide()

        self._apply_color_swatch(swatch, color_value)

        swatch.clicked.connect(lambda: self._pick_setting_color(line_edit, swatch))
        line_edit.editingFinished.connect(lambda: self._apply_color_swatch(swatch, line_edit.text().strip()))

        layout.addWidget(swatch, 0)
        layout.addWidget(line_edit, 0)
        layout.addStretch(1)
        return row

    def _combo(self, items):
        widget = QtWidgets.QComboBox(self)
        widget.setObjectName("RefBoardSettingsCombo")
        widget.addItems(items)
        widget.setMinimumWidth(220)
        widget.setMaximumWidth(280)
        return widget

    def _spin_box(self, value, suffix=""):
        widget = QtWidgets.QSpinBox(self)
        widget.setObjectName("RefBoardSettingsSpinBox")
        widget.setRange(0, 9999)
        widget.setValue(int(value))
        widget.setMinimumWidth(110)
        widget.setMaximumWidth(140)
        if suffix:
            widget.setSuffix(suffix)
        return widget

    def _checkbox(self, text, checked):
        widget = QtWidgets.QCheckBox(text, self)
        widget.setChecked(bool(checked))
        widget.setObjectName("RefBoardSettingsCheckBox")
        return widget

    def _checkbox_only(self, checked):
        return self._checkbox("", checked)

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

    def _reset_placeholder(self):
        QtWidgets.QToolTip.showText(
            self.mapToGlobal(QtCore.QPoint(40, self.height() - 44)),
            "Reset placeholder",
            self,
        )

    def _update_autosave_controls_state(self, enabled):
        for widget in (
            getattr(self, "_autosave_force_spinbox", None),
        ):
            if widget is not None:
                widget.setEnabled(bool(enabled))

    def _update_cache_path_controls_state(self, enabled):
        picker = getattr(self, "_cache_path_picker", None)
        if picker is None:
            return
        line_edit = getattr(picker, "_path_line_edit", None)
        browse_button = getattr(picker, "_browse_button", None)
        if line_edit is not None:
            line_edit.setEnabled(bool(enabled))
        if browse_button is not None:
            browse_button.setEnabled(bool(enabled))

    def _pick_setting_color(self, line_edit, swatch_button):
        current = QtGui.QColor(line_edit.text().strip())
        if not current.isValid():
            current = QtGui.QColor("#ffffff")
        color = QtWidgets.QColorDialog.getColor(current, self, "Choose Color")
        if not color.isValid():
            return
        value = color.name().upper()
        line_edit.setText(value)
        self._apply_color_swatch(swatch_button, value)

    def _apply_color_swatch(self, swatch_button, color_value):
        color = QtGui.QColor((color_value or "").strip())
        if not color.isValid():
            color = QtGui.QColor("#303238")
        swatch_button.setStyleSheet(
            "QPushButton#RefBoardSettingsColorSwatch {{"
            "background: {0};"
            "border: 1px solid #3d4047;"
            "border-radius: 4px;"
            "}}"
            "QPushButton#RefBoardSettingsColorSwatch:hover {{"
            "border: 1px solid #5b6069;"
            "}}".format(color.name())
        )

    def _pick_directory(self, line_edit):
        current = line_edit.text().strip()
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder", current or "")
        if not path:
            return
        line_edit.setText(path)
