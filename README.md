# Nuke RefBoard

Nuke RefBoard is a lightweight reference-board plugin for Foundry Nuke. It adds a floating PySide canvas where artists can collect shot references, notes, checklists, Node Graph jump links, and current-frame links without leaving the Nuke session.

The project is currently a pre-release workflow tool (`0.1.0-pre`) intended for testing and iteration.

## Features

- Infinite-feeling canvas for reference layout work.
- Drag and drop local images, pasted images, and supported remote image URLs.
- Save and load portable `.refboard` files.
- Create multiple boards next to the current Nuke script and switch between them.
- Add editable text notes with font, color, bold, italic, underline, strike-through, and background controls.
- Add checklist notes with clickable checked / unchecked states.
- Copy and paste supported images or text into the board.
- Undo common board actions.
- Move, scale, rotate, delete, and bring board items to front.
- Add NodeMark links that jump back to marked Backdrop nodes in the Nuke Node Graph.
- Add current-frame links that jump the timeline back to saved frames.
- Autosave, cache, canvas, note, and NodeMark preferences.
- Optional always-on-top floating panel pin.

## Requirements

- Foundry Nuke with Python support.
- PySide2 or PySide6 available in the host environment.
- Python 3.7+ is recommended for local development.

Supported image formats:

- `.bmp`
- `.gif`
- `.jpeg`
- `.jpg`
- `.png`
- `.tif`
- `.tiff`
- `.webp`

## Installation

Clone or copy this folder into a location that Nuke can load as a plugin package.

One simple setup is to add the plugin folder from your Nuke `menu.py` or `init.py`:

```python
import nuke

nuke.pluginAddPath(r"F:\R_D\NukeRefBoard")
```

After Nuke starts, the plugin registers a `Nuke RefBoard` menu with:

- `Open Panel`
- `RefBoard NodeMark` in the Node Graph menu, when available

You can also open the floating panel from Nuke's Python console:

```python
import main
main.show_panel()
```

## Basic Usage

1. Save the current Nuke script first.
2. Open `Nuke RefBoard > Open Panel`.
3. Click `New Board` and enter a board identifier.
4. Drag images onto the canvas, paste images or text, or right-click to add notes and links.
5. Use `Save Board` or let autosave keep the board updated.

New boards are saved next to the current Nuke script using this naming pattern:

```text
<nuke_script_name>_boardRef_<identifier>.refboard
```

## Canvas Controls

- Middle mouse drag, or Alt + left mouse drag: pan the canvas.
- Ctrl + mouse wheel: zoom.
- `F`: frame selected items, or all board items when nothing is selected.
- `Delete`: delete selected items.
- `Ctrl+Z`: undo.
- `Ctrl+C`: copy selected board content.
- `Ctrl+V`: paste images or text.
- `Q` / `E`: rotate selected images.
- Right-click canvas: add text, checklist, NodeMark links, frame links, paste, undo, bring to front, or open settings.

## NodeMark Workflow

NodeMarks connect RefBoard notes back to specific areas in the Nuke Node Graph.

1. Select one or more nodes in the Node Graph.
2. Run `RefBoard NodeMark` from the Node Graph menu.
3. Enter a label.
4. In the RefBoard canvas, right-click and choose `Add NodeMark`.
5. Click the created NodeMark link to jump back to the marked backdrop.

NodeMarks are stored as Nuke `BackdropNode` objects with the `RefBoardToolsetBackdrop_` prefix.

## Frame Jump Workflow

Frame jumps store a link to the current Nuke frame.

1. Move the Nuke timeline to the frame you want to remember.
2. Right-click the RefBoard canvas.
3. Choose `Add Current Frame`.
4. Click the created frame link later to jump back to that frame.

## File Format

`.refboard` files are ZIP packages containing:

- `manifest.json`
- `assets/`

The manifest stores canvas view state and board items. Image files are copied into the package so boards can be moved between machines or shared with a shot folder.

Stored item types include:

- `image`
- `note`
- `nodemark`
- `framejump`

## Settings

Open the settings dialog from the toolbar or canvas context menu.

Current settings include:

- Autosave enabled and interval.
- Runtime cache folder and cache cleanup behavior.
- Maximum undo steps.
- Default panel size.
- Debug mode.
- Default note font, size, text color, and background color.
- Checklist continuation behavior.
- NodeMark display style, missing-target behavior, and backdrop color.

Settings are saved per user:

- Windows: `%APPDATA%\NukeRefBoard\settings.json`
- Other platforms: `~/.nuke/NukeRefBoard/settings.json`

## Project Structure

```text
NukeRefBoard/
  init.py                 Nuke plugin path initialization
  menu.py                 Nuke menu registration
  main.py                 Panel registration and floating-panel startup
  session_state.py        User settings load/save helpers
  models/                 Serializable board item data models
  refboard_core/          File format, importer, file manager, NodeMark helpers
  ui/                     PySide panel, canvas, graphics items, dialogs, styles
  resources/icons/        Toolbar and UI icons
  tests/                  Early test modules
```

The `core/` package appears to be a legacy or compatibility copy of some `refboard_core/` modules. New code should prefer `refboard_core/`.

## Development Notes

The panel is built with `QGraphicsView` / `QGraphicsScene`. Board objects are represented by graphics items in `ui/` and serialized through model dataclasses in `models/`.

To test core serialization behavior outside Nuke, keep Nuke-specific imports guarded. The existing code already falls back when `nuke` is unavailable in several modules.

Example local test command:

```bash
python -m pytest tests
```

Some test files are currently placeholders, so passing tests may not yet represent full workflow coverage.

## Status

This is a pre-release build for workflow testing. It is designed for shot-side reference and notes inside Nuke, not as a full PureRef replacement.

