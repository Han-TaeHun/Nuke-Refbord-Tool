# .refboard 파일 저장·불러오기 시리얼라이저
import json
import os
import shutil
import tempfile
import zipfile

from ..models.board_model import BoardModel
from ..models.framejump_model import FrameJumpModel
from ..models.image_model import ImageModel
from ..models.nodemark_model import NodeMarkModel
from ..models.note_model import NoteModel
from .constants import ASSETS_DIRNAME, FORMAT_VERSION, MANIFEST_NAME


class RefBoardSerializer:
    """Read and write .refboard files as ZIP packages with a JSON manifest."""

    def save(
        self,
        file_path,
        board_model,
        image_models,
        note_models=None,
        nodemark_models=None,
        framejump_models=None,
    ):
        temp_dir = tempfile.mkdtemp(prefix="nukerefboard_save_")
        try:
            assets_dir = os.path.join(temp_dir, ASSETS_DIRNAME)
            os.makedirs(assets_dir)
            manifest_items = []
            for index, model in enumerate(image_models, 1):
                source = model.file
                ext = os.path.splitext(source)[1] or ".png"
                asset_name = "img_{0:03d}{1}".format(index, ext.lower())
                asset_path = os.path.join(assets_dir, asset_name)
                if os.path.exists(source):
                    shutil.copy2(source, asset_path)
                saved_model = ImageModel(
                    id=model.id or "img_{0:03d}".format(index),
                    file="{0}/{1}".format(ASSETS_DIRNAME, asset_name),
                    x=model.x,
                    y=model.y,
                    scale=model.scale,
                    rotation=model.rotation,
                    z_order=model.z_order,
                )
                manifest_items.append(saved_model.to_dict())

            for model in note_models or []:
                manifest_items.append(model.to_dict())

            for model in nodemark_models or []:
                manifest_items.append(model.to_dict())

            for model in framejump_models or []:
                manifest_items.append(model.to_dict())

            manifest = {
                "format_version": FORMAT_VERSION,
                "app_name": "Nuke RefBoard",
                "canvas": board_model.to_dict(),
                "items": manifest_items,
            }
            with open(os.path.join(temp_dir, MANIFEST_NAME), "w") as handle:
                json.dump(manifest, handle, indent=2)

            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for root, _, files in os.walk(temp_dir):
                    for filename in files:
                        abs_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(abs_path, temp_dir).replace(os.sep, "/")
                        archive.write(abs_path, rel_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def load(self, file_path, extract_dir):
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        with zipfile.ZipFile(file_path, "r") as archive:
            archive.extractall(extract_dir)
        manifest_path = os.path.join(extract_dir, MANIFEST_NAME)
        with open(manifest_path, "r") as handle:
            manifest = json.load(handle)

        board = BoardModel.from_dict(manifest.get("canvas", {}))
        image_items = []
        note_items = []
        nodemark_items = []
        framejump_items = []
        for item_data in manifest.get("items", []):
            item_type = item_data.get("type")
            if item_type == "image":
                model = ImageModel.from_dict(item_data)
                model.file = os.path.join(extract_dir, model.file.replace("/", os.sep))
                image_items.append(model)
            elif item_type == "note":
                note_items.append(NoteModel.from_dict(item_data))
            elif item_type == "nodemark":
                nodemark_items.append(NodeMarkModel.from_dict(item_data))
            elif item_type == "framejump":
                framejump_items.append(FrameJumpModel.from_dict(item_data))
        return board, image_items, note_items, nodemark_items, framejump_items
