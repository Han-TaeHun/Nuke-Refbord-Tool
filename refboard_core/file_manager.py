# 런타임 파일 및 임시 디렉토리 관리
import shutil
from pathlib import Path


class FileManager:
    """Keeps runtime directories isolated from the plugin source tree."""

    _configured_runtime_root = None

    def __init__(self, namespace="NukeRefBoard", runtime_root=None):
        self.namespace = namespace
        self._runtime_root_override = self._normalize_runtime_root(runtime_root) if runtime_root else None

    @classmethod
    def default_runtime_root(cls) -> str:
        return str(Path(__file__).parent.parent / "temp")

    @classmethod
    def configure_runtime_root(cls, runtime_root=None):
        cls._configured_runtime_root = cls._normalize_runtime_root(runtime_root) if runtime_root else None
        return cls.current_runtime_root()

    @classmethod
    def current_runtime_root(cls) -> str:
        return cls._configured_runtime_root or cls.default_runtime_root()

    @staticmethod
    def _normalize_runtime_root(runtime_root):
        if not runtime_root:
            return None
        return str(Path(runtime_root).resolve())

    @property
    def runtime_dir(self) -> str:
        return self._runtime_root_override or self.current_runtime_root()

    def set_runtime_root(self, runtime_root=None):
        self._runtime_root_override = self._normalize_runtime_root(runtime_root) if runtime_root else None
        return self.runtime_dir

    def ensure_runtime_dir(self) -> str:
        path = Path(self.runtime_dir)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def extraction_dir(self, board_path) -> str:
        base = Path(board_path).stem or "board"
        return str(Path(self.ensure_runtime_dir()) / base)

    def clear_runtime_dir(self):
        runtime_path = Path(self.runtime_dir)
        if not runtime_path.exists():
            return

        default_root = self._normalize_runtime_root(self.default_runtime_root())
        current_root = self._normalize_runtime_root(self.runtime_dir)
        if current_root == default_root:
            shutil.rmtree(runtime_path, ignore_errors=True)
            return

        for child in runtime_path.iterdir():
            try:
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    child.unlink()
            except Exception:
                pass
