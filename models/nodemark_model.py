# NodeMark 링크 데이터 모델
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class NodeMarkModel:
    """Serializable data for one NodeMark hyperlink item."""

    backdrop_name: str = ""
    display_label: str = ""
    id: str = field(default_factory=lambda: "nodemark_{0}".format(uuid4().hex[:10]))
    type: str = "nodemark"
    x: float = 0.0
    y: float = 0.0
    z_order: int = 0

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "backdrop_name": self.backdrop_name,
            "display_label": self.display_label,
            "x": self.x,
            "y": self.y,
            "z_order": self.z_order,
        }

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        return cls(
            id=data.get("id") or "nodemark_{0}".format(uuid4().hex[:10]),
            backdrop_name=data.get("backdrop_name", ""),
            display_label=data.get("display_label", ""),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            z_order=int(data.get("z_order", 0)),
        )
