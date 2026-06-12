# 이미지 에셋 임포터
import shutil
from pathlib import Path
from uuid import uuid4

from .constants import SUPPORTED_IMAGE_EXTENSIONS


class AssetImporter:
    """Normalizes image files into a target asset directory."""

    def __init__(self, asset_dir):
        self.asset_dir = Path(asset_dir)

    def import_file(self, path) -> str:
        if not self.is_supported_image(path):
            raise ValueError("Unsupported image file: {0}".format(path))
        self.asset_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(path).suffix.lower()
        filename = "img_{0}{1}".format(uuid4().hex[:10], ext)
        destination = self.asset_dir / filename
        shutil.copy2(path, destination)
        return str(destination)

    @staticmethod
    def is_supported_image(path) -> bool:
        return bool(path) and Path(path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
