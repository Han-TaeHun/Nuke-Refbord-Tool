# 运行时文件与临时目录管理 / Runtime file and temp directory manager.
import os
import shutil
import tempfile


class FileManager:
    """Keeps runtime directories isolated from the plugin source tree."""

    def __init__(self, namespace="NukeRefBoard"):
        self.namespace = namespace
        self.runtime_dir = os.path.join(tempfile.gettempdir(), namespace)

    def ensure_runtime_dir(self):
        if not os.path.exists(self.runtime_dir):
            os.makedirs(self.runtime_dir)
        return self.runtime_dir

    def extraction_dir(self, board_path):
        base = os.path.splitext(os.path.basename(board_path))[0] or "board"
        return os.path.join(self.ensure_runtime_dir(), base)

    def clear_runtime_dir(self):
        if os.path.exists(self.runtime_dir):
            shutil.rmtree(self.runtime_dir, ignore_errors=True)
