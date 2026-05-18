# 插件启动与面板注册入口 / Plugin startup and panel registration entry point.
"""Nuke RefBoard startup helpers."""

import os
import sys

from refboard_core.constants import PANEL_ID, PLUGIN_NAME
from session_state import current_settings


_floating_panel = None


def _ensure_plugin_path():
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    if plugin_dir not in sys.path:
        sys.path.insert(0, plugin_dir)


def register_panel():
    """Register the dockable Nuke panel."""

    _ensure_plugin_path()
    try:
        import nukescripts
    except ImportError:
        return None
    return nukescripts.panels.registerWidgetAsPanel(
        "ui.panel.RefBoardPanel",
        PLUGIN_NAME,
        PANEL_ID,
        True,
    )


def show_panel():
    """Open the panel from a menu command or Python console."""

    _ensure_plugin_path()
    try:
        from PySide2 import QtCore, QtWidgets
    except ImportError:  # pragma: no cover - for newer host apps
        from PySide6 import QtCore, QtWidgets

    from ui.panel import RefBoardPanel

    global _floating_panel
    existing_panel = _find_existing_floating_panel(QtWidgets)
    if existing_panel is not None:
        _floating_panel = existing_panel
        _show_existing_panel(_floating_panel)
        return _floating_panel

    try:
        if _floating_panel is not None and _floating_panel.isVisible():
            _show_existing_panel(_floating_panel)
            return _floating_panel
    except RuntimeError:
        _floating_panel = None

    _floating_panel = RefBoardPanel()
    _floating_panel.setWindowFlags(_floating_panel.windowFlags() | QtCore.Qt.Window)
    _store_panel_reference(QtWidgets, _floating_panel)
    settings = current_settings()
    _floating_panel.resize(
        int(settings.get("default_panel_width", 1280) or 1280),
        int(settings.get("default_panel_height", 720) or 720),
    )
    _floating_panel.show()
    _floating_panel.raise_()
    _floating_panel.activateWindow()
    return _floating_panel


def _find_existing_floating_panel(QtWidgets):
    app = QtWidgets.QApplication.instance()
    if app is None:
        return None
    for widget in app.topLevelWidgets():
        try:
            if widget.objectName() == "NukeRefBoardPanel" and widget.isVisible():
                return widget
        except RuntimeError:
            continue
    return None


def _show_existing_panel(panel):
    if panel.isMinimized():
        panel.showNormal()
    else:
        panel.show()
    panel.raise_()
    panel.activateWindow()


def _store_panel_reference(QtWidgets, panel):
    app = QtWidgets.QApplication.instance()
    if app is not None:
        app._nuke_refboard_floating_panel = panel
