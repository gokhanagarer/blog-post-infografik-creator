"""`make demo` entrypoint — runs the offline pipeline over examples/prompts.json."""

import os
from pathlib import Path

from .main import main


if __name__ == "__main__":
    os.environ.setdefault("IMAGE_BACKEND", "placeholder")
    project = Path(__file__).resolve().parent.parent
    raise SystemExit(main([
        "--batch", str(project / "examples" / "prompts.json"),
        "--brand", str(project / "assets" / "demo-brand" / "brand.json"),
        "--outdir", str(project / "output"),
    ]))
