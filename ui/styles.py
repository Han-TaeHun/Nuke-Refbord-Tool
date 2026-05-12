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
QToolButton, QPushButton {
    background: #303238;
    border: 1px solid #3d4047;
    border-radius: 4px;
    padding: 5px 9px;
}
QToolButton:hover, QPushButton:hover {
    background: #3a3d45;
}
QToolButton:pressed, QPushButton:pressed {
    background: #4c9aff;
    color: #101114;
}
"""
