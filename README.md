# Nuke RefBoard Dev Branch

This branch is for live development inside Nuke. The most important workflow is using the Nuke menu command as a lightweight hot-reload shortcut while editing Python files.

## Dev Setup

Point Nuke at this working copy:

```python
nuke.pluginAddPath(r"F:\R_D\NukeRefBoard")
```

Restart Nuke once after adding the path. You should see:

- `Nuke RefBoard > Open Panel`
- `Node Graph > RefBoard NodeMark`

## Hot Reload Workflow

The dev menu entry reloads project modules before opening the panel.

Typical loop:

1. Edit files in this working copy.
2. Close the current RefBoard panel in Nuke.
3. Click `Nuke RefBoard > Open Panel`.
4. Test the change.
5. Repeat.

The reload shortcut clears these module groups from `sys.modules`:

- `main`
- `ui`
- `models`
- `refboard_core`
- `core`

Then it imports `main.show_panel()` again, so most UI, model, serializer, and helper changes are picked up without restarting Nuke.

## Important Reload Note

If the RefBoard panel is already open, `Open Panel` only raises the existing window and does not rebuild it. Close the panel first when testing UI or constructor changes.

For changes to Nuke startup registration, menu creation, or plugin path setup, restart Nuke. Those parts run when Nuke loads `init.py` / `menu.py`.

## Console Shortcut

You can also run this from Nuke's Python console:

```python
import menu
menu.open_refboard_panel()
```

This uses the same reload path as the menu command.

## Debug Mode

Open RefBoard settings and enable `Debug mode` to expose extra test actions in the context menu, including loading overlay and save toast checks.

## Quick Checks

Useful things to verify after a reload:

- The panel opens without import errors.
- Drag-and-drop image import still works.
- Notes and checklists can be created from the canvas context menu.
- Save / load still produces a valid `.refboard` file.
- NodeMark links still jump to the expected Backdrop node.
- Frame links still jump to the expected Nuke frame.

## When To Restart Nuke

Restart Nuke when changing:

- `init.py`
- top-level menu registration behavior in `menu.py`
- plugin search paths
- Nuke callback registration
- code that left broken Qt objects alive in the current session

For normal UI and logic edits, closing the panel and reopening it from the RefBoard menu should be enough.

