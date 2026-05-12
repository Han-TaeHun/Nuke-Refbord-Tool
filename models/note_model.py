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
