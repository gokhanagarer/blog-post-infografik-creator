"""Offline pipeline tests."""

import os
from pathlib import Path

from PIL import Image

from src.brand import Brand
from src.generators import PillowPlaceholderGenerator, get
from src.main import generate_and_process, main


ROOT = Path(__file__).resolve().parent.parent
BRAND_JSON = ROOT / "assets" / "demo-brand" / "brand.json"
PROMPTS_JSON = ROOT / "examples" / "prompts.json"


def test_brand_loads_with_resolved_logo_path():
    b = Brand.load(BRAND_JSON)
    assert b.name == "Acme"
    assert b.logo_path.exists()
    assert b.colors["primary_blue"] == (0, 96, 217)


def test_placeholder_generator_writes_real_image(tmp_path):
    g = PillowPlaceholderGenerator(brand=Brand.load(BRAND_JSON))
    out = tmp_path / "x.png"
    g.generate("hello world infographic", out, width=640, height=360)
    assert out.exists() and out.stat().st_size > 1000
    with Image.open(out) as im:
        assert im.size == (640, 360)


def test_factory_returns_placeholder_when_no_backend_set(monkeypatch):
    monkeypatch.delenv("IMAGE_BACKEND", raising=False)
    g = get()
    assert isinstance(g, PillowPlaceholderGenerator)


def test_generate_and_process_writes_jpg_with_logo(tmp_path):
    brand = Brand.load(BRAND_JSON)
    out = tmp_path / "hero.jpg"
    generate_and_process("test prompt", out, image_type="hero", brand=brand,
                         backend="placeholder", width=640, height=360)
    assert out.exists() and out.stat().st_size > 1000
    with Image.open(out) as im:
        assert im.format == "JPEG"


def test_main_batch_demo(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_BACKEND", "placeholder")
    rc = main(["--batch", str(PROMPTS_JSON),
               "--brand", str(BRAND_JSON),
               "--outdir", str(tmp_path)])
    assert rc == 0
    files = sorted(tmp_path.glob("*.jpg"))
    assert len(files) == 3
    for f in files:
        assert f.stat().st_size > 1000
