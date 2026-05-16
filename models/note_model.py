# 文字注释数据模型 / Text note annotation data model.
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class NoteModel:
    """Future text annotation data model."""

    text: str = ""
    id: str = field(default_factory=lambda: "note_{0}".format(uuid4().hex[:10]))
    type: str = "note"
    x: float = 0.0
    y: float = 0.0
    z_order: int = 0
    style: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "z_order": self.z_order,
            "style": dict(self.style or {}),
        }

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        return cls(
            id=data.get("id") or "note_{0}".format(uuid4().hex[:10]),
            type=data.get("type", "note"),
            text=data.get("text", ""),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            z_order=int(data.get("z_order", 0)),
            style=dict(data.get("style") or {}),
        )
