# 메인 도킹 가능 레퍼런스 보드 패널 컨트롤러
import ctypes
import os
import re

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - for newer host apps
    from PySide6 import QtCore, QtGui, QtWidgets

try:
    import nuke
except ImportError:  # pragma: no cover - allows local UI testing outside Nuke
    nuke = None

try:
    from flova.ui.widget import FlovaDialog
    from flova.ui import img_path as _img_path
    _HAS_FLOVA_UI = True
except ImportError:
    _HAS_FLOVA_UI = False
    FlovaDialog = QtWidgets.QWidget
    _img_path = None

from ..refboard_core.constants import FILE_EXTENSION, PLUGIN_NAME
from ..refboard_core.file_manager import FileManager
from ..refboard_core.serializer import RefBoardSerializer
from ..session_state import current_settings, update_settings
from .canvas_view import RefCanvasView
from .settings_dialog import RefBoardSettingsDialog
from .status_overlay import RefBoardLoadingOverlay, RefBoardSaveToast
from .styles import PANEL_STYLE

# 툴 아이콘 경로 (W: 드라이브 직접 참조)
_SYMBOL_ICON_PATH = "W:/inhouse/icons/reference_board/symbol.png"
_PIN_ICON_PATH = "W:/inhouse/icons/reference_board/pin.png"


class RefBoardPanel(FlovaDialog):
    """Floating Nuke RefBoard panel with the first interactive canvas."""

    def __init__(self, parent=None):
        if _HAS_FLOVA_UI:
            super().__init__(
                "NukeRefBoardPanel", parent,
                app_title=PLUGIN_NAME,
                app_icon=_SYMBOL_ICON_PATH,
                app_description="Nuke에서 레퍼런스 이미지, 노트, 체크리스트, NodeMark를 관리하는 보드 툴",
                app_doc_url="https://book.infx.kr/books/tool/page/reference-board",
            )
        else:
            super().__init__(parent)
            self.setObjectName("NukeRefBoardPanel")

        # 창 타이틀바 아이콘 교체 (FlovaDialog 기본 로고 대신)
        if os.path.exists(_SYMBOL_ICON_PATH):
            self.setWindowIcon(QtGui.QIcon(_SYMBOL_ICON_PATH))
        self._is_pinned = False
        self._is_dirty = False
        self._suspend_dirty_tracking = False
        self._current_board_path = None
        self._settings = current_settings()
        self._icon_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources",
            "icons",
        )
        self._serializer = RefBoardSerializer()
        self._file_manager = FileManager()
        self._settings_dialog = None
        self._autosave_timer = QtCore.QTimer(self)
        self._autosave_timer.timeout.connect(self._autosave_if_needed)
        self._build_ui()
        self._apply_runtime_settings(self._settings)

    def _build_ui(self):
        super().ui()  # FlovaDialog.ui(): window_layout(배너 포함) + main_layout 생성
        self.setStyleSheet(PANEL_STYLE)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)

        self.toolbar = QtWidgets.QFrame(self)
        self.toolbar.setObjectName("RefBoardToolbarPlaceholder")
        self.toolbar.setFixedHeight(37)
        toolbar_layout = QtWidgets.QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)
        toolbar_layout.setSpacing(6)

        self.new_board_button = self._toolbar_button("새 보드", "새 보드 만들기")
        self.switch_board_button = self._toolbar_button("보드 전환", "다른 보드로 전환")
        self.import_board_button = self._toolbar_button("가져오기", "기존 .refboard 가져오기")
        self.save_board_button = self._toolbar_button("저장", "현재 보드 저장")
        self.save_as_board_button = self._toolbar_button("다른 이름으로", "다른 이름으로 저장")
        self.settings_button = self._toolbar_button("설정", "RefBoard 설정")
        self.board_identifier_label = QtWidgets.QLabel(self.toolbar)
        self.board_identifier_label.setObjectName("RefBoardBoardIdentifierLabel")
        self.board_identifier_label.setAlignment(QtCore.Qt.AlignCenter)
        self.board_identifier_label.setFixedWidth(180)
        self.board_identifier_label.setText("")
        self.board_identifier_label.setProperty("hasIdentifier", False)
        self.pin_button = QtWidgets.QToolButton(self.toolbar)
        self.pin_button.setObjectName("RefBoardPinButton")
        self.pin_button.setToolTip("패널을 항상 위에 유지")
        self.pin_button.setCheckable(True)
        self.pin_button.setAutoRaise(False)
        self.pin_button.setIconSize(QtCore.QSize(22, 22))
        self.pin_button.setFixedHeight(30)
        self.pin_button.toggled.connect(self._set_window_pinned)
        self._update_pin_button_icon(False)
        self.search_edit = QtWidgets.QLineEdit(self.toolbar)
        self.search_edit.setObjectName("RefBoardSearchEdit")
        self.search_edit.setPlaceholderText("검색...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setFixedWidth(160)
        self.search_edit.setFixedHeight(26)
        self._set_toolbar_button_icon(self.new_board_button, "icon_NewBoard.svg")
        self._set_toolbar_button_icon(self.switch_board_button, "icon_SwitchBoard.svg")
        self._set_toolbar_button_icon(self.import_board_button, "icon_ImportBoard.svg")
        self._set_toolbar_button_icon(self.save_board_button, "icon_Save.svg")
        self._set_toolbar_button_icon(self.save_as_board_button, "icon_SaveAs.svg")
        self._set_toolbar_button_icon(self.settings_button, "icon_Setting.svg")

        toolbar_layout.addWidget(self.new_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.import_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.switch_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.save_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.save_as_board_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self._toolbar_separator(), 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.settings_button, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.board_identifier_label, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.search_edit, 0, QtCore.Qt.AlignVCenter)
        toolbar_layout.addWidget(self.pin_button, 0, QtCore.Qt.AlignVCenter)

        self.canvas = RefCanvasView(self)
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas, 1)
        self.loading_overlay = RefBoardLoadingOverlay(self)
        self.save_toast = RefBoardSaveToast(self)
        self.search_edit.installEventFilter(self)
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.canvas.boardChanged.connect(self._on_board_changed)
        self.new_board_button.clicked.connect(self._handle_new_board_clicked)
        self.import_board_button.clicked.connect(self._import_board)
        self.save_board_button.clicked.connect(self._save_board)
        self.save_as_board_button.clicked.connect(self._save_board_as)
        self.switch_board_button.clicked.connect(self._switch_board)
        self.settings_button.clicked.connect(self._open_settings_dialog)

    def _toolbar_button(self, text, tooltip):
        button = QtWidgets.QToolButton(self.toolbar)
        button.setObjectName("RefBoardToolbarButton")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setAutoRaise(False)
        button.setIconSize(QtCore.QSize(20, 20))
        button.setFixedHeight(29)
        return button

    def _set_toolbar_button_icon(self, button, icon_name):
        icon_path = os.path.join(self._icon_dir, icon_name)
        if not os.path.exists(icon_path):
            return
        button.setIcon(QtGui.QIcon(icon_path))
        button.setText("")
        button.setFixedWidth(36)

    def _toolbar_separator(self):
        separator = QtWidgets.QFrame(self.toolbar)
        separator.setObjectName("RefBoardToolbarSeparator")
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Plain)
        separator.setFixedWidth(14)
        separator.setFixedHeight(18)
        return separator

    def _open_settings_dialog(self):
        if self._settings_dialog is None:
            self._settings_dialog = RefBoardSettingsDialog(self)
            self._settings_dialog.settingsApplied.connect(self._apply_settings)
        self._settings_dialog.load_settings(self._settings)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def open_settings_dialog(self):
        self._open_settings_dialog()

    def debug_mode_enabled(self):
        return bool(self._settings.get("debug_mode"))

    def _handle_new_board_clicked(self):
        if not self._confirm_safe_board_change("create a new board"):
            return
        if self._nuke_scene_requires_save():
            QtWidgets.QMessageBox.information(
                self,
                "씬 저장 필요",
                "먼저 현재 Nuke 씬을 저장하세요.",
            )
            return
        identifier = self._prompt_new_board_identifier()
        if identifier is None:
            return
        board_path = self._resolve_new_board_path(identifier)
        if not board_path:
            return  # 사용자가 파일 다이얼로그를 취소함
        if os.path.exists(board_path):
            reply = QtWidgets.QMessageBox.question(
                self,
                "보드가 이미 존재합니다",
                "같은 이름의 보드가 이미 있습니다.\n\n덮어쓰시겠습니까?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
        self._new_board(board_path)

    def _new_board(self, board_path=None):
        self._suspend_dirty_tracking = True
        self.canvas.clear_board()
        self._suspend_dirty_tracking = False
        self._current_board_path = None
        self._set_dirty(False)
        if board_path:
            self._save_board_to_path(board_path)

    def _import_board(self):
        if not self._confirm_safe_board_change("다른 보드 가져오기"):
            return
        ref_board_dir = self._get_ref_board_dir(create=False)
        initial_dir = ref_board_dir if ref_board_dir else os.path.join(os.path.expanduser("~"), "Desktop")
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "RefBoard 열기",
            initial_dir,
            "RefBoard 파일 (*{0})".format(FILE_EXTENSION),
        )
        if not file_path:
            return
        self._load_board_from_path(file_path)

    def _switch_board(self):
        if not self._confirm_safe_board_change("보드 전환"):
            return
        search_dir = self._get_switch_board_search_dir()
        if not search_dir:
            QtWidgets.QMessageBox.information(
                self,
                "씬 저장 필요",
                "먼저 현재 Nuke 씬을 저장하세요.",
            )
            return
        board_choices = self._scene_board_choices(search_dir)
        if not board_choices:
            QtWidgets.QMessageBox.information(
                self,
                "RefBoard 없음",
                "검색 경로에서 .refboard 파일을 찾을 수 없습니다.",
            )
            return

        labels = [choice[0] for choice in board_choices]
        selected_label, accepted = QtWidgets.QInputDialog.getItem(
            self,
            "보드 전환",
            "보드를 선택하세요:",
            labels,
            0,
            False,
        )
        if not accepted or not selected_label:
            return

        for label, file_path in board_choices:
            if label == selected_label:
                self._load_board_from_path(file_path)
                return

    def _save_board(self):
        if not self._current_board_path:
            return self._save_board_as()
        return self._save_board_to_path(self._current_board_path)

    def _save_board_as(self):
        file_path = self._prompt_save_path()
        return self._save_board_to_path(file_path)

    def _save_board_to_path(self, file_path):
        if not file_path:
            return False
        try:
            self._serializer.save(
                file_path,
                self.canvas.board_model(),
                self.canvas.image_models(),
                self.canvas.note_models(),
                self.canvas.nodemark_models(),
                self.canvas.framejump_models(),
            )
        except Exception as exc:
            self.save_toast.show_error_bottom_left("RefBoard 저장 실패")
            self._show_save_failure_message(exc)
            return False
        self._current_board_path = file_path
        self._set_dirty(False)
        self.save_toast.show_bottom_left("RefBoard 저장됨")
        return True

    def _prompt_save_path(self):
        ref_board_dir = self._get_ref_board_dir(create=True)
        initial_dir = ref_board_dir if ref_board_dir else os.path.join(os.path.expanduser("~"), "Desktop")
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "RefBoard 저장",
            initial_dir,
            "RefBoard 파일 (*{0})".format(FILE_EXTENSION),
        )
        if not file_path:
            return None
        if not file_path.lower().endswith(FILE_EXTENSION):
            file_path += FILE_EXTENSION
        return file_path

    def _prompt_new_board_identifier(self):
        identifier, accepted = QtWidgets.QInputDialog.getText(
            self,
            "새 보드 만들기",
            "보드 식별자 (현재 Nuke 씬 옆에 저장됩니다):",
        )
        if not accepted:
            return None
        identifier = self._sanitize_board_identifier(identifier)
        if not identifier:
            QtWidgets.QMessageBox.information(
                self,
                "식별자 필요",
                "유효한 보드 식별자를 입력하세요.",
            )
            return None
        return identifier

    def _sanitize_board_identifier(self, identifier):
        text = (identifier or "").strip()
        text = re.sub(r"\s+", "_", text)
        text = re.sub(r'[<>:"/\\|?*]+', "_", text)
        text = re.sub(r"_+", "_", text).strip("._")
        return text

    def _get_ref_board_dir(self, create=True):
        """WorkPath.is_valid()가 참이면 wip/ref_board 경로 반환, 거짓이면 None 반환.

        Args:
            create: True면 경로가 없을 때 생성한다.

        Returns:
            str | None: wip/ref_board 절대 경로, 또는 None.
        """
        scene_path = self._current_nuke_scene_path()
        if not scene_path:
            return None
        try:
            from flova.path import WorkPath, ShotWorkPath, AssetWorkPath
            wp = WorkPath(scene_path)
            if wp.is_valid():
                wip_ref = None
                if wp.is_shot_entity():
                    wip_ref = ShotWorkPath(
                        wp.project_code(), wp.sequence(), wp.shot_code(), wp.step_code()
                    ).wip('ref_board')
                elif wp.is_asset_entity():
                    wip_ref = AssetWorkPath(
                        wp.project_code(), wp.asset_type(), wp.asset_code(), wp.step_code()
                    ).wip('ref_board')
                if wip_ref:
                    if create:
                        os.makedirs(wip_ref, exist_ok=True)
                    return wip_ref
        except Exception:
            pass
        return None

    def _get_switch_board_search_dir(self):
        """보드 전환 검색 경로를 반환한다.

        is_valid()이고 ref_board 폴더가 이미 있으면 그 폴더,
        아니면 씬 파일 디렉토리를 반환한다.

        Returns:
            str | None: 검색 디렉토리, 씬 미저장이면 None.
        """
        scene_path = self._current_nuke_scene_path()
        if not scene_path:
            return None
        ref_board_dir = self._get_ref_board_dir(create=False)
        if ref_board_dir and os.path.isdir(ref_board_dir):
            return ref_board_dir
        return os.path.dirname(scene_path)

    def _resolve_new_board_path(self, identifier):
        """새 보드 저장 경로를 결정한다.

        is_valid()이면 wip/ref_board/ 에 자동 경로,
        아니면 파일 다이얼로그를 열어 사용자가 선택한 경로를 반환한다.
        취소 시 None 반환.

        Args:
            identifier: 보드 식별자 문자열.

        Returns:
            str | None: 저장 경로, 또는 None.
        """
        scene_path = self._current_nuke_scene_path()
        if not scene_path:
            return None
        scene_name = os.path.splitext(os.path.basename(scene_path))[0]
        file_name = "{0}_boardRef_{1}{2}".format(scene_name, identifier, FILE_EXTENSION)
        ref_board_dir = self._get_ref_board_dir(create=True)
        if ref_board_dir:
            return os.path.join(ref_board_dir, file_name)
        # is_valid() False: 파일 다이얼로그로 위치 선택
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "새 보드 저장 위치 선택",
            os.path.join(desktop, file_name),
            "RefBoard 파일 (*{0})".format(FILE_EXTENSION),
        )
        if not file_path:
            return None
        if not file_path.lower().endswith(FILE_EXTENSION):
            file_path += FILE_EXTENSION
        return file_path

    def _load_board_from_path(self, file_path):
        extract_dir = self._file_manager.extraction_dir(file_path)
        self.loading_overlay.show_centered()
        QtWidgets.QApplication.processEvents()
        try:
            board_model, image_models, note_models, nodemark_models, framejump_models = self._serializer.load(
                file_path, extract_dir
            )
            self._suspend_dirty_tracking = True
            self.canvas.load_board(board_model, image_models, note_models, nodemark_models, framejump_models)
            self._suspend_dirty_tracking = False
            self._current_board_path = file_path
            self._set_dirty(False)
        except Exception as exc:
            self.save_toast.show_error_bottom_left("RefBoard 불러오기 실패")
            self._show_load_failure_message(exc)
            return False
        finally:
            self._suspend_dirty_tracking = False
            self.loading_overlay.hide()
        return True

    def _set_window_pinned(self, pinned):
        self._is_pinned = bool(pinned)
        self._update_pin_button_icon(self._is_pinned)
        # SetWindowPos로 topmost 설정 — setWindowFlag+show() 방식은 창 재생성으로 깜빡임 발생
        _HWND_TOPMOST = -1
        _HWND_NOTOPMOST = -2
        _SWP_NOMOVE = 0x0002
        _SWP_NOSIZE = 0x0001
        _SWP_NOACTIVATE = 0x0010
        try:
            hwnd = int(self.winId())
            z_order = _HWND_TOPMOST if pinned else _HWND_NOTOPMOST
            ctypes.windll.user32.SetWindowPos(hwnd, z_order, 0, 0, 0, 0, _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOACTIVATE)
        except Exception:
            self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, self._is_pinned)
            self.show()
            self.raise_()
            self.activateWindow()

    def _update_pin_button_icon(self, pinned):
        if os.path.exists(_PIN_ICON_PATH):
            self.pin_button.setIcon(QtGui.QIcon(_PIN_ICON_PATH))
            self.pin_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        else:
            self.pin_button.setIcon(QtGui.QIcon())
            self.pin_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.pin_button.setText("고정됨" if pinned else "고정")

    def eventFilter(self, obj, event):
        # search_edit에서 Enter 키가 dialog 기본 버튼을 트리거하지 않도록 소비
        if obj is self.search_edit and event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "loading_overlay") and self.loading_overlay.isVisible():
            self.loading_overlay.show_centered()
        if hasattr(self, "save_toast") and self.save_toast.isVisible():
            self.save_toast.reposition_bottom_left()

    def closeEvent(self, event):
        if not self._is_dirty:
            self._cleanup_runtime_cache_if_needed()
            super().closeEvent(event)
            return

        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowTitle("저장되지 않은 변경사항")
        message_box.setText("보드에 저장되지 않은 변경사항이 있습니다.")
        message_box.setInformativeText("닫기 전에 저장하시겠습니까?")
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        save_button = message_box.addButton("저장", QtWidgets.QMessageBox.AcceptRole)
        discard_button = message_box.addButton("저장 안 함", QtWidgets.QMessageBox.DestructiveRole)
        cancel_button = message_box.addButton("취소", QtWidgets.QMessageBox.RejectRole)
        message_box.setDefaultButton(save_button)
        message_box.exec_()

        clicked = message_box.clickedButton()
        if clicked == save_button:
            if self._save_board():
                self._cleanup_runtime_cache_if_needed()
                super().closeEvent(event)
                event.accept()
            else:
                event.ignore()
            return
        if clicked == discard_button:
            self._cleanup_runtime_cache_if_needed()
            super().closeEvent(event)
            event.accept()
            return
        if clicked == cancel_button:
            event.ignore()
            return
        event.ignore()

    def contextMenuEvent(self, event):
        if not self.debug_mode_enabled():
            return
        menu = QtWidgets.QMenu(self)
        debug_menu = menu.addMenu("개발 디버그 테스트")
        toggle_loading_action = debug_menu.addAction("로딩 오버레이 테스트")
        hide_loading_action = debug_menu.addAction("로딩 오버레이 숨기기")
        debug_menu.addSeparator()
        test_save_toast_action = debug_menu.addAction("저장 토스트 테스트")
        test_save_error_toast_action = debug_menu.addAction("저장 실패 토스트 테스트")
        hide_save_toast_action = debug_menu.addAction("저장 토스트 숨기기")
        action = menu.exec_(event.globalPos())
        if action == toggle_loading_action:
            self.loading_overlay.show_centered()
        elif action == hide_loading_action:
            self.loading_overlay.hide()
        elif action == test_save_toast_action:
            self.save_toast.show_bottom_left("RefBoard 저장됨")
        elif action == test_save_error_toast_action:
            self.save_toast.show_error_bottom_left("RefBoard save failed")
        elif action == hide_save_toast_action:
            self.save_toast.hide()

    def _on_search_changed(self, query):
        self.canvas.filter_items(query)
        q = query.strip().lower()
        if not q:
            effect = self.board_identifier_label.graphicsEffect()
            if effect:
                effect.setOpacity(1.0)
        else:
            label_text = self.board_identifier_label.text().lower()
            opacity = 1.0 if q in label_text else 0.15
            effect = self.board_identifier_label.graphicsEffect()
            if not isinstance(effect, QtWidgets.QGraphicsOpacityEffect):
                effect = QtWidgets.QGraphicsOpacityEffect(self.board_identifier_label)
                self.board_identifier_label.setGraphicsEffect(effect)
            effect.setOpacity(opacity)

    def _on_board_changed(self):
        if self._suspend_dirty_tracking:
            return
        self._set_dirty(True)

    def _set_dirty(self, dirty):
        self._is_dirty = bool(dirty)
        title = PLUGIN_NAME
        if self._current_board_path:
            title = "{0} - {1}".format(PLUGIN_NAME, os.path.basename(self._current_board_path))
        if self._is_dirty:
            title += " *"
        self.setWindowTitle(title)
        self._update_board_identifier_display()
        self.canvas.viewport().update()

    def set_max_undo_steps(self, steps):
        return self.canvas.set_max_undo_steps(steps)

    def max_undo_steps(self):
        return self.canvas.max_undo_steps()

    def _show_save_failure_message(self, exc):
        message = str(exc).strip() or exc.__class__.__name__
        QtWidgets.QMessageBox.warning(
            self,
            "저장 실패",
            "RefBoard를 저장할 수 없습니다.\n\n{0}".format(message),
        )

    def _show_load_failure_message(self, exc):
        message = str(exc).strip() or exc.__class__.__name__
        QtWidgets.QMessageBox.warning(
            self,
            "불러오기 실패",
            "RefBoard를 불러올 수 없습니다.\n\n{0}".format(message),
        )

    def empty_state_message(self):
        if self._nuke_scene_requires_save():
            return u"먼저 Nuke 씬을 저장하세요"
        if not self._current_board_path:
            return u"새 보드 만들기, 보드 전환, 또는 .refboard 가져오기"
        return u">>>  이미지를 여기에 드래그하세요  <<<"

    def _apply_settings(self, settings):
        self._settings = update_settings(settings)
        self._apply_runtime_settings(self._settings)

    def _apply_runtime_settings(self, settings):
        settings = settings or {}
        custom_cache_enabled = bool(settings.get("use_custom_cache_directory"))
        configured_cache_dir = (settings.get("cache_directory") or "").strip()
        runtime_root = configured_cache_dir if custom_cache_enabled and configured_cache_dir else None
        FileManager.configure_runtime_root(runtime_root)
        self._file_manager.set_runtime_root(runtime_root)
        self.canvas.file_manager.set_runtime_root(runtime_root)
        self.canvas.apply_settings(settings)
        self.canvas.set_max_undo_steps(settings.get("max_undo_steps", 50))
        self._update_autosave_timer()
        self.resize(
            int(settings.get("default_panel_width", self.width()) or self.width()),
            int(settings.get("default_panel_height", self.height()) or self.height()),
        )

    def _update_autosave_timer(self):
        enabled = bool(self._settings.get("autosave_enabled"))
        interval_minutes = max(1, int(self._settings.get("autosave_interval_minutes", 10) or 10))
        if not enabled:
            self._autosave_timer.stop()
            return
        self._autosave_timer.start(interval_minutes * 60 * 1000)

    def _autosave_if_needed(self):
        if not self._settings.get("autosave_enabled"):
            return
        if not self._is_dirty or not self._current_board_path:
            return
        self._save_board_to_path(self._current_board_path)

    def _cleanup_runtime_cache_if_needed(self):
        if not self._settings.get("clean_cache_on_exit", True):
            return
        try:
            self._file_manager.clear_runtime_dir()
        except Exception:
            pass

    def _confirm_safe_board_change(self, action_label="계속"):
        if not self._is_dirty:
            return True
        QtWidgets.QMessageBox.information(
            self,
            "저장되지 않은 보드",
            "{0} 전에 현재 보드를 저장하세요.".format(action_label),
        )
        return False

    def _nuke_scene_requires_save(self):
        return not bool(self._current_nuke_scene_path())

    def _current_nuke_scene_path(self):
        if nuke is None:
            return None
        try:
            root = nuke.root()
            if root is None:
                return None
            scene_path = root.name() or ""
            if scene_path == "Root":
                return None
            return scene_path
        except Exception:
            return None

    def _current_scene_base_name(self):
        scene_path = self._current_nuke_scene_path()
        if not scene_path:
            return None
        return os.path.splitext(os.path.basename(scene_path))[0]

    def _scene_board_choices(self, search_dir):
        if not search_dir or not os.path.isdir(search_dir):
            return []
        board_paths = []
        try:
            for name in sorted(os.listdir(search_dir)):
                if not name.lower().endswith(FILE_EXTENSION):
                    continue
                board_paths.append(os.path.join(search_dir, name))
        except OSError:
            return []

        used_labels = set()
        choices = []
        for board_path in board_paths:
            label = self._switch_board_label_for_path(board_path)
            unique_label = label
            suffix = 2
            while unique_label in used_labels:
                unique_label = "{0} ({1})".format(label, suffix)
                suffix += 1
            used_labels.add(unique_label)
            choices.append((unique_label, board_path))
        return choices

    def _switch_board_label_for_path(self, file_path):
        identifier = self._board_identifier_for_path(file_path)
        file_name = os.path.basename(file_path)
        if identifier:
            return "{0} - {1}".format(identifier, file_name)
        return os.path.splitext(file_name)[0]

    def _board_identifier_for_path(self, file_path):
        if not file_path:
            return ""
        scene_base_name = self._current_scene_base_name()
        if not scene_base_name:
            return ""
        file_name = os.path.basename(file_path)
        pattern = r"^{0}_boardRef_(.+){1}$".format(
            re.escape(scene_base_name),
            re.escape(FILE_EXTENSION),
        )
        match = re.match(pattern, file_name, re.IGNORECASE)
        if not match:
            return ""
        return match.group(1)

    def _update_board_identifier_display(self):
        if not self._current_board_path:
            text = "= 식별자 없음 ="
            has_identifier = False
        else:
            identifier = self._board_identifier_for_path(self._current_board_path)
            # 씬 미저장·패턴 불일치 시 파일명(확장자 제외)으로 폴백
            text = identifier or os.path.splitext(os.path.basename(self._current_board_path))[0]
            has_identifier = True
        self.board_identifier_label.setProperty("hasIdentifier", has_identifier)
        self.board_identifier_label.setText(text)
        self.board_identifier_label.style().unpolish(self.board_identifier_label)
        self.board_identifier_label.style().polish(self.board_identifier_label)
        self.board_identifier_label.update()
