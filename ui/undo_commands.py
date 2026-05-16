# 画板撤销命令 / Board undo command helpers.
try:
    from PySide2 import QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtWidgets


class AddBoardItemCommand(QtWidgets.QUndoCommand):
    """Add a single board item to the canvas scene."""

    def __init__(self, view, item, label):
        super(AddBoardItemCommand, self).__init__(label)
        self.view = view
        self.item = item

    def redo(self):
        self.view._add_item_to_scene(self.item, select=True)

    def undo(self):
        self.view._remove_item_from_scene(self.item)


class RemoveBoardItemsCommand(QtWidgets.QUndoCommand):
    """Remove one or more selected items from the canvas scene."""

    def __init__(self, view, items, label):
        super(RemoveBoardItemsCommand, self).__init__(label)
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


class ItemStateChangeCommand(QtWidgets.QUndoCommand):
    """Undoable move / rotate / scale state change for one item."""

    def __init__(self, view, item, before_state, after_state, label):
        super(ItemStateChangeCommand, self).__init__(label)
        self.view = view
        self.item = item
        self.before_state = dict(before_state or {})
        self.after_state = dict(after_state or {})

    def redo(self):
        self.view._apply_item_state(self.item, self.after_state)

    def undo(self):
        self.view._apply_item_state(self.item, self.before_state)
