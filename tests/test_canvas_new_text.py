#New Text 行为回归测试  #New Text behavior regression tests

import os
import unittest

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    try:
        from PySide6 import QtCore, QtWidgets
    except ImportError:
        QtCore = None
        QtWidgets = None


@unittest.skipIf(QtWidgets is None, "PySide is not available in this Python environment")
class CanvasNewTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        from ui.canvas_view import RefCanvasView

        self.view = RefCanvasView()
        self.view.resize(640, 480)
        self.view.show()
        self.app.processEvents()

    def tearDown(self):
        self.view.close()
        self.view.deleteLater()
        self.app.processEvents()

    def test_add_note_adds_selected_editable_note_at_scene_position(self):
        scene_pos = QtCore.QPointF(123.0, 456.0)

        note = self.view.add_note(scene_pos=scene_pos)
        self.app.processEvents()

        self.assertIsNotNone(note)
        self.assertIs(note.scene(), self.view.scene())
        self.assertEqual(note.toPlainText(), "Text")
        self.assertEqual(note.pos(), scene_pos)
        self.assertTrue(note.isSelected())
        self.assertIs(self.view.scene().focusItem(), note)
        self.assertTrue(note.is_editing())
        self.assertIn(note, self.view.note_items())

    def test_add_note_respects_auto_enter_edit_setting(self):
        self.view.apply_settings({"auto_enter_edit_mode_for_new_text": False})

        note = self.view.add_note(scene_pos=QtCore.QPointF(10.0, 20.0))
        self.app.processEvents()

        self.assertTrue(note.isSelected())
        self.assertIs(self.view.scene().focusItem(), note)
        self.assertFalse(note.is_editing())


if __name__ == "__main__":
    unittest.main()
