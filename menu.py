# 注册 Nuke 菜单入口 / Registers the Nuke menu entry.
"""Nuke menu registration for Nuke RefBoard."""

import os
import sys

from refboard_core.constants import PLUGIN_NAME


PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
RELOAD_MODULES = (
    "main",
    "ui",
    "models",
    "refboard_core",
    "core",
)


def _ensure_plugin_path():
    if PLUGIN_DIR in sys.path:
        sys.path.remove(PLUGIN_DIR)
    sys.path.insert(0, PLUGIN_DIR)


def _reload_plugin_modules():
    """Reload project modules so the menu works as a development shortcut."""

    _ensure_plugin_path()
    for name in list(sys.modules.keys()):
        if name == __name__:
            continue
        for module_name in RELOAD_MODULES:
            if name == module_name or name.startswith(module_name + "."):
                del sys.modules[name]
                break


def open_refboard_panel():
    """Reload the plugin code and open the floating panel."""

    _reload_plugin_modules()
    from main import show_panel

    return show_panel()


def create_refboard_nodemark():
    """Create a NodeMark backdrop from the current Node Graph selection."""

    _reload_plugin_modules()
    from refboard_core.nodemark import create_nodemark_from_selection

    return create_nodemark_from_selection()


_ensure_plugin_path()

try:
    import nuke
except ImportError:
    nuke = None

if nuke is not None:
    menu = nuke.menu("Nuke")
    refboard_menu = menu.addMenu(PLUGIN_NAME)
    refboard_menu.addCommand("Open Panel", open_refboard_panel)
    try:
        node_graph_menu = nuke.menu("Node Graph")
        node_graph_menu.addCommand("RefBoard NodeMark", create_refboard_nodemark)
    except Exception:
        pass
