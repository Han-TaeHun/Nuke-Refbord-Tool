# NodeMark 节点创建与跳转辅助 / NodeMark backdrop creation and jump helpers.
import re

from refboard_core.constants import (
    NODEMARK_BACKDROP_COLOR,
    NODEMARK_DEFAULT_LABEL,
    NODEMARK_PREFIX,
)
from session_state import current_settings


def create_nodemark_from_selection():
    nuke = _get_nuke_module()
    if nuke is None:
        return None

    selected_nodes = list(nuke.selectedNodes())
    if not selected_nodes:
        nuke.message("Select one or more nodes in the Node Graph first.")
        return None

    label = nuke.getInput("RefBoard NodeMark label", NODEMARK_DEFAULT_LABEL)
    if label is None:
        return None

    label = label.strip()
    if not label:
        nuke.message("NodeMark creation cancelled because the label was empty.")
        return None

    bbox = _selection_bbox(selected_nodes)
    if bbox is None:
        return None

    label_slug = _slugify_label(label)
    node_name = _unique_backdrop_name(label_slug, nuke)
    return nuke.nodes.BackdropNode(
        xpos=bbox["x"],
        ypos=bbox["y"],
        bdwidth=bbox["width"],
        bdheight=bbox["height"],
        tile_color=int(_configured_backdrop_color()),
        note_font_size=32,
        label=label_slug,
        name=node_name,
    )


def list_nodemark_backdrops():
    nuke = _get_nuke_module()
    if nuke is None:
        return []

    nodemarks = []
    for node in nuke.allNodes("BackdropNode"):
        name = node.name()
        if not name.startswith(NODEMARK_PREFIX):
            continue
        label = _display_label_for_node(node)
        nodemarks.append(
            {
                "name": name,
                "label": label,
            }
        )
    nodemarks.sort(key=lambda item: item["label"].lower())
    return nodemarks


def jump_to_nodemark(backdrop_name):
    nuke = _get_nuke_module()
    if nuke is None:
        return False

    backdrop = nuke.toNode(backdrop_name)
    if backdrop is None or backdrop.Class() != "BackdropNode":
        return False

    for node in nuke.allNodes():
        try:
            node.setSelected(False)
        except Exception:
            pass

    backdrop.setSelected(True)
    try:
        backdrop.selectNodes(True)
    except Exception:
        pass

    if hasattr(nuke, "zoomToFitSelected"):
        nuke.zoomToFitSelected()
        return True

    nuke.zoom(1, [backdrop.xpos(), backdrop.ypos()])
    return True


def _selection_bbox(nodes):
    if not nodes:
        return None

    rects = [_node_rect(node) for node in nodes]
    min_x = min(rect["x"] for rect in rects)
    min_y = min(rect["y"] for rect in rects)
    max_x = max(rect["x"] + rect["width"] for rect in rects)
    max_y = max(rect["y"] + rect["height"] for rect in rects)

    label_band_height = 56
    padding_left = 80
    padding_right = 80
    padding_top = 96
    padding_bottom = 90
    return {
        "x": int(min_x - padding_left),
        "y": int(min_y - padding_top),
        "width": int((max_x - min_x) + padding_left + padding_right),
        "height": int((max_y - min_y) + padding_top + padding_bottom + label_band_height),
    }


def _node_rect(node):
    width = node.screenWidth() if hasattr(node, "screenWidth") else 100
    height = node.screenHeight() if hasattr(node, "screenHeight") else 60
    x = int(node.xpos())
    y = int(node.ypos())
    if hasattr(node, "Class") and node.Class() == "BackdropNode":
        try:
            width = int(node["bdwidth"].value())
            height = int(node["bdheight"].value())
        except Exception:
            pass
    return {
        "x": x,
        "y": y,
        "width": int(width),
        "height": int(height),
    }


def _unique_backdrop_name(label_slug, nuke):
    base_name = "{0}{1}".format(NODEMARK_PREFIX, label_slug)
    if nuke.toNode(base_name) is None:
        return base_name

    index = 1
    while True:
        candidate = "{0}_{1:02d}".format(base_name, index)
        if nuke.toNode(candidate) is None:
            return candidate
        index += 1


def _slugify_label(label):
    slug = label.replace(" ", "_")
    slug = re.sub(r"[^0-9A-Za-z_]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or NODEMARK_DEFAULT_LABEL


def _display_label_for_node(node):
    try:
        label = node["label"].value().strip()
        if label:
            return label
    except Exception:
        pass
    name = node.name()
    if name.startswith(NODEMARK_PREFIX):
        return name[len(NODEMARK_PREFIX):]
    return name


def _get_nuke_module():
    try:
        import nuke
    except ImportError:
        return None
    return nuke


def _configured_backdrop_color():
    color_value = current_settings().get("nodemark_backdrop_color", "#2F4F6F")
    if isinstance(color_value, str):
        text = color_value.strip().lstrip("#")
        if len(text) == 6:
            try:
                return int("{0}FF".format(text), 16)
            except ValueError:
                pass
    return NODEMARK_BACKDROP_COLOR
