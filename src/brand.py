"""Brand configuration loader. Brand is purely data — palette + logo path."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Brand:
    name: str
    colors: dict[str, tuple[int, int, int]]
    logo_path: Path

    @classmethod
    def load(cls, json_path: str | Path) -> "Brand":
        p = Path(json_path)
        data = json.loads(p.read_text(encoding="utf-8"))
        colors = {k: tuple(v) for k, v in data["colors"].items()}
        logo = p.parent / data["logo"] if not Path(data["logo"]).is_absolute() else Path(data["logo"])
        return cls(name=data["name"], colors=colors, logo_path=logo)
