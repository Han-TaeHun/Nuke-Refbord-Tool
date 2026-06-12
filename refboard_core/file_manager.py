# 런타임 파일 및 임시 디렉토리 관리
import os
import shutil


class FileManager:
    """Keeps runtime directories isolated from the plugin source tree."""

    _configured_runtime_root = None

    def __init__(self, namespace="NukeRefBoard", runtime_root=None):
        self.namespace = namespace
        self._runtime_root_override = self._normalize_runtime_root(runtime_root) if runtime_root else None

    @classmethod
    def default_runtime_root(cls):
        plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(plugin_root, "temp")

    @classmethod
    def configure_runtime_root(cls, runtime_root=None):
        cls._configured_runtime_root = cls._normalize_runtime_root(runtime_root) if runtime_root else None
        return cls.current_runtime_root()

    @classmethod
    def current_runtime_root(cls):
        return cls._configured_runtime_root or cls.default_runtime_root()

    @staticmethod
    def _normalize_runtime_root(runtime_root):
        if not runtime_root:
            return None
        return os.path.abspath(os.path.normpath(runtime_root))

    @property
    def runtime_dir(self):
        return self._runtime_root_override or self.current_runtime_root()

    def set_runtime_root(self, runtime_root=None):
        self._runtime_root_override = self._normalize_runtime_root(runtime_root) if runtime_root else None
        return self.runtime_dir

    def ensure_runtime_dir(self):
        if not os.path.exists(self.runtime_dir):
            os.makedirs(self.runtime_dir)
        return self.runtime_dir

    def extraction_dir(self, board_path):
        base = os.path.splitext(os.path.basename(board_path))[0] or "board"
        return os.path.join(self.ensure_runtime_dir(), base)

    def clear_runtime_dir(self):
        runtime_dir = self.runtime_dir
        if not os.path.exists(runtime_dir):
            return

        default_root = self._normalize_runtime_root(self.default_runtime_root())
        current_root = self._normalize_runtime_root(runtime_dir)
        if current_root == default_root:
            shutil.rmtree(runtime_dir, ignore_errors=True)
            return

        for name in os.listdir(runtime_dir):
            path = os.path.join(runtime_dir, name)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
            except Exception:
                pass
