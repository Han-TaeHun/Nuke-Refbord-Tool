# 프레임 점프 하이퍼링크 데이터 모델
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class FrameJumpModel:
    """Serializable data for one frame-jump hyperlink item."""

    frame: int = 1
    display_label: str = ""
    id: str = field(default_factory=lambda: "framejump_{0}".format(uuid4().hex[:10]))
    type: str = "framejump"
    x: float = 0.0
    y: float = 0.0
    z_order: int = 0

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "frame": self.frame,
            "display_label": self.display_label,
            "x": self.x,
            "y": self.y,
            "z_order": self.z_order,
        }

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        return cls(
            id=data.get("id") or "framejump_{0}".format(uuid4().hex[:10]),
            frame=int(data.get("frame", 1)),
            display_label=data.get("display_label", ""),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            z_order=int(data.get("z_order", 0)),
        )
