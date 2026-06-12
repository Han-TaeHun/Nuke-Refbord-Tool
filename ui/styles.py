# UI 색상 및 QSS 스타일시트 (노랑/회색 톤앤매너)
BACKGROUND = "#202124"
CANVAS_BACKGROUND = "#17181a"
PANEL_BORDER = "#323438"
TEXT = "#e7e7e7"
ACCENT = "#f2cb58"


PANEL_STYLE = """
QWidget {
    background: #202124;
    color: #e7e7e7;
    font-size: 12px;
}
QToolBar {
    background: #25272b;
    border: 0;
    border-bottom: 1px solid #323438;
    spacing: 4px;
}
QFrame#RefBoardToolbarPlaceholder {
    background: #25272b;
    border: 0;
    border-bottom: 1px solid #3a3a3a;
}
QFrame#RefBoardToolbarSeparator {
    background: #3b3e45;
    border: 0;
    margin-left: 6px;
    margin-right: 6px;
}
QLabel#RefBoardBoardIdentifierLabel {
    min-height: 22px;
    padding: 0 10px;
    font-size: 12px;
}
QLabel#RefBoardBoardIdentifierLabel[hasIdentifier="true"] {
    color: #f2cb58;
    font-weight: 700;
}
QLabel#RefBoardBoardIdentifierLabel[hasIdentifier="false"] {
    color: #7f8693;
    font-weight: 500;
    font-style: italic;
}
QFrame#RefBoardFloatingTextToolbar {
    background: #25272b;
    border: 1px solid #3d4047;
    border-radius: 6px;
}
QFrame#RefBoardLoadingOverlay {
    background: rgba(25, 27, 31, 230);
    border: 1px solid #454a53;
    border-radius: 12px;
}
QFrame#RefBoardSaveToast {
    background: rgba(40, 36, 18, 235);
    border: 1px solid #7a6a1a;
    border-radius: 10px;
}
QFrame#RefBoardSaveToast[toastVariant="error"] {
    background: rgba(64, 22, 24, 235);
    border: 1px solid #8e4448;
    border-radius: 10px;
}
QLabel#RefBoardLoadingTitle {
    color: #f1f3f5;
    background: transparent;
    font-size: 18px;
    font-weight: 600;
}
QLabel#RefBoardLoadingBody {
    color: #a7adb7;
    background: transparent;
    font-size: 12px;
}
QLabel#RefBoardSaveToastText {
    color: #f2cb58;
    background: transparent;
    font-size: 12px;
    font-weight: 600;
}
QLabel#RefBoardSaveToastText[toastVariant="error"] {
    color: #ffd9da;
}
QToolButton, QPushButton {
    background: #4d4d4d;
    border: 1px solid #2e2e2e;
    border-radius: 4px;
    padding: 5px 9px;
    color: #dddddd;
}
QToolButton:hover, QPushButton:hover {
    background: #5d5d5d;
    border: 1px solid #666666;
    color: #ffffff;
}
QToolButton:checked {
    background: #3a3a3a;
    color: #dddddd;
    border: 1px solid #555555;
}
QToolButton:pressed, QPushButton:pressed {
    background: #3a3a3a;
    color: #dddddd;
}
QPushButton:disabled, QToolButton:disabled {
    background: #3a3a3a;
    border: 1px solid #2a2a2a;
    color: #666666;
}
QToolButton#RefBoardPinButton {
    background: #4d4d4d;
    border: 1px solid #2e2e2e;
    border-radius: 4px;
    padding: 4px 10px;
    color: #aaaaaa;
    font-weight: 500;
}
QToolButton#RefBoardPinButton:hover {
    background: #5d5d5d;
    border: 1px solid #777777;
    color: #ffffff;
}
QToolButton#RefBoardPinButton:checked {
    background: #b05500;
    border: 1px solid #d07020;
    color: #ffffff;
    font-weight: 700;
}
QToolButton#RefBoardPinButton:checked:hover {
    background: #c06200;
    border: 1px solid #e08030;
}
QLineEdit#RefBoardSearchEdit {
    background: #383838;
    border: 1px solid #444444;
    border-radius: 4px;
    color: #dddddd;
    padding: 2px 6px;
    selection-background-color: #5a5a5a;
}
QLineEdit#RefBoardSearchEdit:focus {
    border: 1px solid #666666;
    background: #404040;
}
QMenu {
    background: #25272b;
    border: 1px solid #3d4047;
    color: #e7e7e7;
    padding: 4px;
}
QMenu::item {
    padding: 5px 26px 5px 22px;
    background: transparent;
}
QMenu::item:selected {
    background: #3a3d45;
    color: #f2cb58;
}
QMenu::item:disabled {
    color: #4f545d;
    background: transparent;
}
QMenu::separator {
    height: 1px;
    background: #3b3e45;
    margin: 4px 8px;
}
QFontComboBox#RefBoardFontComboBox, QSpinBox#RefBoardFontSizeBox {
    background: #18191c;
    border: 1px solid #3d4047;
    border-radius: 4px;
    padding: 4px 6px;
    color: #e7e7e7;
}
QSpinBox#RefBoardFontSizeBox {
    min-width: 62px;
}
QDialog#RefBoardSettingsDialog {
    background: #26282c;
}
QFrame#RefBoardSettingsFrame {
    background: #2b2d31;
    border: 1px solid #3b3e45;
    border-radius: 8px;
}
QFrame#RefBoardSettingsNavPanel {
    background: #33353a;
    border: 1px solid #3e4249;
    border-radius: 6px;
    min-width: 260px;
    max-width: 260px;
}
QTreeWidget#RefBoardSettingsTree {
    background: transparent;
    border: 0;
    outline: none;
}
QTreeWidget#RefBoardSettingsTree::item {
    min-height: 24px;
    padding-left: 8px;
}
QTreeWidget#RefBoardSettingsTree::item:selected {
    background: #f2cb58;
    color: #1a1a1a;
}
QTreeWidget#RefBoardSettingsTree::item:hover {
    background: #3a3d45;
}
QFrame#RefBoardSettingsPagePanel {
    background: transparent;
    border: 0;
}
QLabel#RefBoardSettingsPageTitle {
    color: #f3f5f7;
    font-size: 20px;
    font-weight: 600;
    padding-bottom: 4px;
}
QLabel#RefBoardSettingsSectionTitle {
    color: #f2f4f6;
    font-size: 13px;
    font-weight: 600;
    border-bottom: 1px solid #444850;
    padding-bottom: 4px;
}
QLabel#RefBoardSettingsFieldLabel {
    color: #d5d8de;
}
QLineEdit#RefBoardSettingsLineEdit,
QComboBox#RefBoardSettingsCombo,
QSpinBox#RefBoardSettingsSpinBox,
QTableWidget#RefBoardSettingsTable {
    background: #232529;
    border: 1px solid #3d4047;
    border-radius: 4px;
    color: #eceef2;
    padding: 4px 6px;
}
QSpinBox#RefBoardSettingsSpinBox {
    padding-right: 20px;
}
QLineEdit#RefBoardSettingsLineEdit:disabled,
QComboBox#RefBoardSettingsCombo:disabled,
QSpinBox#RefBoardSettingsSpinBox:disabled,
QTableWidget#RefBoardSettingsTable:disabled {
    background: #1b1d20;
    border: 1px solid #30333a;
    color: #7b8088;
}
QComboBox#RefBoardSettingsCombo::drop-down {
    border: 0;
    width: 20px;
}
QSpinBox#RefBoardSettingsSpinBox::up-button,
QSpinBox#RefBoardSettingsSpinBox::down-button {
    subcontrol-origin: border;
    width: 18px;
    background: #2f3237;
    border-left: 1px solid #454a53;
}
QSpinBox#RefBoardSettingsSpinBox::up-button {
    subcontrol-position: top right;
    border-top-right-radius: 4px;
}
QSpinBox#RefBoardSettingsSpinBox::down-button {
    subcontrol-position: bottom right;
    border-bottom-right-radius: 4px;
    border-top: 1px solid #454a53;
}
QSpinBox#RefBoardSettingsSpinBox::up-button:hover,
QSpinBox#RefBoardSettingsSpinBox::down-button:hover {
    background: #3a3d45;
}
QSpinBox#RefBoardSettingsSpinBox::up-arrow,
QSpinBox#RefBoardSettingsSpinBox::down-arrow {
    width: 8px;
    height: 8px;
}
QTableWidget#RefBoardSettingsTable {
    gridline-color: #3d4047;
}
QTableWidget#RefBoardSettingsTable QHeaderView::section {
    background: #2f3237;
    color: #eceef2;
    border: 0;
    border-right: 1px solid #3d4047;
    padding: 6px;
}
QFrame#RefBoardSettingsPlaceholderBox {
    background: #232529;
    border: 1px solid #3d4047;
    border-radius: 6px;
}
QLabel#RefBoardSettingsPlaceholderText {
    color: #aeb4bf;
}
QLabel#RefBoardAboutTitle {
    color: #f3f5f7;
    font-size: 26px;
    font-weight: 700;
}
QLabel#RefBoardAboutVersion {
    color: #f2cb58;
    font-size: 13px;
    font-weight: 600;
}
QLabel#RefBoardAboutBody {
    color: #c9ced6;
    font-size: 13px;
    line-height: 150%;
}
QPushButton#RefBoardSettingsMiniButton {
    min-width: 30px;
    min-height: 30px;
    padding: 0;
}
"""
