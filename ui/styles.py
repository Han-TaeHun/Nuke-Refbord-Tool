# UI 颜色与 QSS 样式 / UI colors and QSS stylesheet.
BACKGROUND = "#202124"
CANVAS_BACKGROUND = "#17181a"
PANEL_BORDER = "#323438"
TEXT = "#e7e7e7"
ACCENT = "#4c9aff"


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
    border-bottom: 1px solid #323438;
}
QFrame#RefBoardToolbarSeparator {
    background: #3b3e45;
    border: 0;
    margin-left: 6px;
    margin-right: 6px;
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
    background: rgba(27, 42, 33, 235);
    border: 1px solid #42634c;
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
    color: #d8f2de;
    background: transparent;
    font-size: 12px;
    font-weight: 600;
}
QLabel#RefBoardSaveToastText[toastVariant="error"] {
    color: #ffd9da;
}
QToolButton, QPushButton {
    background: #303238;
    border: 1px solid #3d4047;
    border-radius: 4px;
    padding: 5px 9px;
}
QToolButton:hover, QPushButton:hover {
    background: #3a3d45;
}
QToolButton:checked {
    background: #4c9aff;
    color: #101114;
}
QToolButton:pressed, QPushButton:pressed {
    background: #4c9aff;
    color: #101114;
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
"""
