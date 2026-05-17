# 帧跳转链接数据模型 / Frame jump hyperlink data model.
class FrameJumpModel(object):
    """Serializable data for one frame-jump hyperlink item."""

    def __init__(self, frame=1, display_label="", id="", x=0.0, y=0.0, z_order=0):
        self.id = id or ""
        self.type = "framejump"
        self.frame = int(frame)
        self.display_label = display_label
        self.x = float(x)
        self.y = float(y)
        self.z_order = int(z_order)

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
            id=data.get("id", ""),
            frame=int(data.get("frame", 1)),
            display_label=data.get("display_label", ""),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            z_order=int(data.get("z_order", 0)),
        )
