"""Orchestrator: prompt(s) → generated image(s) → branded post-processed image(s)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from . import generators, postprocess
from .brand import Brand

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("infografik")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BRAND = ROOT / "assets" / "demo-brand" / "brand.json"
DEFAULT_OUTPUT = ROOT / "output"
DEFAULT_PROMPTS = ROOT / "examples" / "prompts.json"


def generate_and_process(
    prompt: str,
    output_path: Path,
    *,
    image_type: postprocess.ImageType = "hero",
    width: int = 1920,
    height: int = 1080,
    brand: Brand | None = None,
    backend: str | None = None,
) -> Path:
    gen = generators.get(backend, brand=brand)
    with tempfile.TemporaryDirectory() as tmpdir:
        raw = Path(tmpdir) / "raw.png"
        gen.generate(prompt, raw, width=width, height=height)
        return postprocess.process(raw, output_path, image_type=image_type, brand=brand)


def run_batch(prompts_path: Path, outdir: Path, *, brand: Brand, backend: str | None) -> int:
    items = json.loads(prompts_path.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        log.error("prompts file must be a JSON list of {prompt, filename, type}")
        return 1

    outdir.mkdir(parents=True, exist_ok=True)
    failed = 0
    for i, item in enumerate(items, 1):
        prompt = item["prompt"]
        filename = item["filename"]
        image_type = item.get("type", "hero")
        out = outdir / filename
        log.info("[%d/%d] %s (%s)", i, len(items), filename, image_type)
        try:
            generate_and_process(prompt, out, image_type=image_type, brand=brand, backend=backend)
            log.info("  saved → %s", out)
        except Exception:  # noqa: BLE001
            log.exception("  failed")
            failed += 1
    return failed


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate + brand-process blog infographics")
    p.add_argument("prompt", nargs="?", help="single prompt (or use --batch)")
    p.add_argument("output", nargs="?", help="single output JPG path")
    p.add_argument("--type", default="hero", choices=["hero", "info", "photo"])
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--brand", type=Path, default=DEFAULT_BRAND, help="brand.json file")
    p.add_argument("--backend", choices=["placeholder", "pollinations", "gemini"], default=None)
    p.add_argument("--batch", type=Path, help="JSON file with list of prompts")
    p.add_argument("--outdir", type=Path, default=DEFAULT_OUTPUT, help="batch output directory")
    args = p.parse_args(argv)

    brand = Brand.load(args.brand) if args.brand and args.brand.exists() else None

    if args.batch:
        failed = run_batch(args.batch, args.outdir, brand=brand, backend=args.backend)
        return 1 if failed else 0

    if not args.prompt or not args.output:
        p.error("prompt and output are required (or use --batch)")

    try:
        out = generate_and_process(
            args.prompt, Path(args.output),
            image_type=args.type, width=args.width, height=args.height,
            brand=brand, backend=args.backend,
        )
        log.info("saved → %s", out)
        return 0
    except Exception:  # noqa: BLE001
        log.exception("failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
