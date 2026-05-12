# 插件启动与面板注册入口 / Plugin startup and panel registration entry point.
"""Nuke RefBoard startup helpers."""

import os
import sys

from refboard_core.constants import PANEL_ID, PLUGIN_NAME


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
        import nuke
        import nukescripts
    except ImportError:
        from ui.panel import RefBoardPanel

        panel = RefBoardPanel()
        panel.show()
        return panel

    pane = nuke.getPaneFor("Properties.1")
    restored_panel = nukescripts.panels.restorePanel(PANEL_ID)
    if restored_panel is not None:
        return restored_panel

    registered_panel = register_panel()
    if registered_panel is None:
        return None
    if pane is not None:
        return registered_panel.addToPane(pane)
    return registered_panel
