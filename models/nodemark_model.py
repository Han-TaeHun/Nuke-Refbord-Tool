# NodeMark 链接数据模型 / NodeMark link data model.
class NodeMarkModel(object):
    """Serializable data for one NodeMark hyperlink item."""

    def __init__(self, backdrop_name="", display_label="", id="", x=0.0, y=0.0, z_order=0):
        self.id = id or ""
        self.type = "nodemark"
        self.backdrop_name = backdrop_name
        self.display_label = display_label
        self.x = float(x)
        self.y = float(y)
        self.z_order = int(z_order)

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
            id=data.get("id", ""),
            backdrop_name=data.get("backdrop_name", ""),
            display_label=data.get("display_label", ""),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            z_order=int(data.get("z_order", 0)),
        )
