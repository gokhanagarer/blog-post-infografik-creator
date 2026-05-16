"""Image post-processor: brand colour boost, subtle vignette, logo overlay."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageEnhance

from .brand import Brand

ImageType = Literal["hero", "info", "photo"]


def _svg_to_png(svg_path: Path, width: int, height: int) -> Image.Image:
    """Rasterise an SVG with cairosvg.

    cairosvg requires the native libcairo library to be installed
    (`brew install cairo` on macOS, `apt-get install libcairo2` on Debian/Ubuntu).
    If it's not available, raise so the caller can choose to fall back.
    """
    import cairosvg  # noqa: PLC0415 — local import so we can detect missing libcairo gracefully
    png_bytes = cairosvg.svg2png(
        url=str(svg_path), output_width=width, output_height=height, background_color="transparent",
    )
    return Image.open(BytesIO(png_bytes)).convert("RGBA")


def add_logo(image: Image.Image, logo_path: Path, *, size_percent: float = 12, padding: int = 40) -> Image.Image:
    img_w, _ = image.size
    logo_w = int(img_w * (size_percent / 100))

    if logo_path.suffix.lower() == ".svg":
        try:
            logo = _svg_to_png(logo_path, logo_w, logo_w)
        except (ImportError, OSError):
            # cairo isn't available — look for a sibling PNG of the same name.
            png_sibling = logo_path.with_suffix(".png")
            if png_sibling.exists():
                logo_path = png_sibling
            else:
                raise
    if logo_path.suffix.lower() != ".svg":
        logo = Image.open(logo_path).convert("RGBA")
        aspect = logo.height / logo.width
        logo = logo.resize((logo_w, int(logo_w * aspect)))

    pos = (img_w - logo.width - padding, padding)
    base = image.convert("RGBA")
    base.paste(logo, pos, logo)
    return base.convert("RGB")


def enhance_colors(image: Image.Image, *, color_boost: float = 1.2, contrast_boost: float = 1.1) -> Image.Image:
    image = ImageEnhance.Color(image).enhance(color_boost)
    image = ImageEnhance.Contrast(image).enhance(contrast_boost)
    return image


def subtle_vignette(image: Image.Image, *, intensity: float = 0.2) -> Image.Image:
    w, h = image.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    for i in range(255):
        alpha = int(255 * (1 - intensity * (i / 255)))
        bbox = [i * w // 510, i * h // 510, w - i * w // 510, h - i * h // 510]
        draw.ellipse(bbox, fill=alpha)
    vignette = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(image, vignette, mask)


_PROFILES: dict[ImageType, dict[str, float]] = {
    "hero":  {"color_boost": 1.30, "contrast_boost": 1.10, "vignette": 0.20},
    "info":  {"color_boost": 1.10, "contrast_boost": 1.05, "vignette": 0.00},
    "photo": {"color_boost": 1.15, "contrast_boost": 1.05, "vignette": 0.15},
}


def process(
    input_path: str | Path,
    output_path: str | Path,
    *,
    image_type: ImageType = "hero",
    brand: Brand | None = None,
    logo_size_percent: float = 12,
    logo_padding: int = 40,
) -> Path:
    """Apply the brand-consistent post-process pipeline; return the output path."""
    image = Image.open(input_path)
    if image.mode != "RGB":
        image = image.convert("RGB")

    profile = _PROFILES[image_type]
    image = enhance_colors(image, color_boost=profile["color_boost"], contrast_boost=profile["contrast_boost"])
    if profile["vignette"] > 0:
        image = subtle_vignette(image, intensity=profile["vignette"])

    if brand is not None and brand.logo_path.exists():
        image = add_logo(image, brand.logo_path, size_percent=logo_size_percent, padding=logo_padding)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, "JPEG", quality=95, optimize=True)
    return out
