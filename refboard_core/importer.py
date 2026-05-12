# 图片资产导入器 / Image asset importer for board resources.
import os
import shutil
from uuid import uuid4

from refboard_core.constants import SUPPORTED_IMAGE_EXTENSIONS


class AssetImporter:
    """Normalizes image files into a target asset directory."""

    def __init__(self, asset_dir):
        self.asset_dir = asset_dir

    def import_file(self, path):
        if not self.is_supported_image(path):
            raise ValueError("Unsupported image file: {0}".format(path))
        if not os.path.exists(self.asset_dir):
            os.makedirs(self.asset_dir)
        ext = os.path.splitext(path)[1].lower()
        filename = "img_{0}{1}".format(uuid4().hex[:10], ext)
        destination = os.path.join(self.asset_dir, filename)
        shutil.copy2(path, destination)
        return destination

    @staticmethod
    def is_supported_image(path):
        return bool(path) and os.path.splitext(path)[1].lower() in SUPPORTED_IMAGE_EXTENSIONS
