# 보드 실행취소 커맨드
try:
    from PySide2 import QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtWidgets


class AddBoardItemCommand(QtWidgets.QUndoCommand):
    """Add a single board item to the canvas scene."""

    def __init__(self, view, item, label):
        super().__init__(label)
        self.view = view
        self.item = item

    def redo(self):
        self.view._add_item_to_scene(self.item, select=True)

    def undo(self):
        self.view._remove_item_from_scene(self.item)


class RemoveBoardItemsCommand(QtWidgets.QUndoCommand):
    """Remove one or more selected items from the canvas scene."""

    def __init__(self, view, items, label):
        super().__init__(label)
        self.view = view
        self.items = list(items or [])

    def redo(self):
        for item in self.items:
            self.view._remove_item_from_scene(item)

    def undo(self):
        for item in self.items:
            self.view._add_item_to_scene(item)
        if self.items:
            self.view.scene().clearSelection()
            for item in self.items:
                item.setSelected(True)
            self.view.viewport().update()


class BringBoardItemsToFrontCommand(QtWidgets.QUndoCommand):
    """Move selected board items above the rest of the canvas."""

    def __init__(self, view, items, label):
        super().__init__(label)
        self.view = view
        self.items = list(items or [])
        self.before_z_values = [(item, float(item.zValue())) for item in self.items]
        self.after_z_values = []

    def redo(self):
        if not self.after_z_values:
            next_z = self.view._next_z_value()
            self.after_z_values = []
            for index, item in enumerate(sorted(self.items, key=lambda board_item: board_item.zValue())):
                self.after_z_values.append((item, float(next_z + index)))
        self._apply_z_values(self.after_z_values)

    def undo(self):
        self._apply_z_values(self.before_z_values)

    def _apply_z_values(self, z_values):
        for item, z_value in z_values:
            item.setZValue(z_value)
        self.view.scene().clearSelection()
        for item, _ in z_values:
            item.setSelected(True)
        self.view._notify_scene_changed()


class ItemStateChangeCommand(QtWidgets.QUndoCommand):
    """Undoable move / rotate / scale state change for one item."""

    def __init__(self, view, item, before_state, after_state, label):
        super().__init__(label)
        self.view = view
        self.item = item
        self.before_state = dict(before_state or {})
        self.after_state = dict(after_state or {})

    def redo(self):
        self.view._apply_item_state(self.item, self.after_state)

    def undo(self):
        self.view._apply_item_state(self.item, self.before_state)
