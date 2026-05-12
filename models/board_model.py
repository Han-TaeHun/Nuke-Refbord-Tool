# 画布状态数据模型 / Board viewport state data model.
from dataclasses import dataclass


@dataclass
class BoardModel:
    """Serializable canvas state."""

    zoom: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0

    def to_dict(self):
        return {
            "zoom": self.zoom,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
        }

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        return cls(
            zoom=float(data.get("zoom", 1.0)),
            offset_x=float(data.get("offset_x", 0.0)),
            offset_y=float(data.get("offset_y", 0.0)),
        )
