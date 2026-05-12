# 单张图片数据模型 / Single reference image data model.
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class ImageModel:
    """Serializable data for one reference image."""

    file: str
    id: str = field(default_factory=lambda: "img_{0}".format(uuid4().hex[:10]))
    type: str = "image"
    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0
    rotation: float = 0.0
    z_order: int = 0

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "file": self.file,
            "x": self.x,
            "y": self.y,
            "scale": self.scale,
            "rotation": self.rotation,
            "z_order": self.z_order,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id") or "img_{0}".format(uuid4().hex[:10]),
            type=data.get("type", "image"),
            file=data.get("file", ""),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            scale=float(data.get("scale", 1.0)),
            rotation=float(data.get("rotation", 0.0)),
            z_order=int(data.get("z_order", 0)),
        )
