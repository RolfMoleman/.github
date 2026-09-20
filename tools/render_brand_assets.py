#!/usr/bin/env python3
"""Render deterministic RolfMoleman GitHub and JustGiving banner assets."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "source" / "downatthebottomofthemolehole_banner_20.png"
OUTPUT_DIR = ROOT / "assets" / "banners"
LOCAL_FONT = ROOT / "assets" / "fonts" / "stonehen.ttf"

PARCHMENT = (232, 215, 181, 255)
GOLD = (209, 164, 94, 255)
GOLD_DARK = (111, 71, 40, 255)
INK = (11, 9, 7, 255)
BLUE = (102, 210, 255, 255)
STONEHENGE_SHA256 = "ce21460833ed97837924bdaaa1455530ad330562dd73e80f0242fa0d4b879810"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--font",
        type=Path,
        default=Path(os.environ.get("STONEHENGE_FONT", LOCAL_FONT)),
        help="Path to the exact stonehen.ttf file (or set STONEHENGE_FONT).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=SOURCE,
        help="Path to the unmodified banner_20 source artwork.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory in which to write the generated PNG files.",
    )
    return parser.parse_args()


def validate_font(font_path: Path) -> None:
    if not font_path.is_file():
        raise SystemExit(
            f"Stonehenge font not found at {font_path}. "
            "Download stonehen.ttf and pass it with --font."
        )

    try:
        family, style = ImageFont.truetype(font_path, 32).getname()
    except OSError as error:
        raise SystemExit(f"Unable to load font at {font_path}: {error}") from error

    if family.casefold() != "stonehenge":
        raise SystemExit(
            f"Expected the Stonehenge typeface, received {family} {style}. "
            "No fallback font will be used."
        )

    digest = hashlib.sha256(font_path.read_bytes()).hexdigest()
    if digest != STONEHENGE_SHA256:
        raise SystemExit(
            "The supplied Stonehenge file does not match the approved render "
            f"dependency (received SHA-256 {digest})."
        )


def cover_crop(source: Image.Image, size: tuple[int, int], focus_y: float) -> Image.Image:
    """Crop around a vertical focal point and resize without stretching."""
    target_width, target_height = size
    target_ratio = target_width / target_height
    source_width, source_height = source.size
    source_ratio = source_width / source_height

    if source_ratio < target_ratio:
        crop_height = source_width / target_ratio
        centre_y = source_height * focus_y
        top = max(0.0, min(source_height - crop_height, centre_y - crop_height / 2))
        box = (0.0, top, float(source_width), top + crop_height)
    else:
        crop_width = source_height * target_ratio
        left = (source_width - crop_width) / 2
        box = (left, 0.0, left + crop_width, float(source_height))

    return source.crop(box).resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def fit_font(
    font_path: Path,
    text: str,
    max_width: int,
    max_height: int,
    maximum_size: int,
    stroke_width: int,
) -> ImageFont.FreeTypeFont:
    for size in range(maximum_size, 9, -1):
        font = ImageFont.truetype(font_path, size)
        left, top, right, bottom = font.getbbox(text, stroke_width=stroke_width)
        if right - left <= max_width and bottom - top <= max_height:
            return font
    raise ValueError(f"Unable to fit display text: {text}")


def text_size(
    text: str, font: ImageFont.FreeTypeFont, stroke_width: int
) -> tuple[int, int, int, int]:
    left, top, right, bottom = font.getbbox(text, stroke_width=stroke_width)
    return left, top, right - left, bottom - top


def draw_display_text(
    image: Image.Image,
    font_path: Path,
    text: str,
    box: tuple[int, int, int, int],
    maximum_size: int,
    *,
    fill: tuple[int, int, int, int] = PARCHMENT,
    stroke_width: int = 3,
) -> None:
    x0, y0, x1, y1 = box
    font = fit_font(
        font_path,
        text,
        x1 - x0,
        y1 - y0,
        maximum_size,
        stroke_width,
    )
    left, top, width, height = text_size(text, font, stroke_width)
    x = x0 + ((x1 - x0) - width) / 2 - left
    y = y0 + ((y1 - y0) - height) / 2 - top

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.text(
        (x + 5, y + 7),
        text,
        font=font,
        fill=(0, 0, 0, 220),
        stroke_width=stroke_width + 3,
        stroke_fill=(0, 0, 0, 210),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(2.2))
    image.alpha_composite(shadow)

    draw = ImageDraw.Draw(image)
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=INK,
    )
    draw.text((x, y - 1), text, font=font, fill=(248, 232, 198, 105))


def add_text_panel(image: Image.Image, start_x: int, maximum_alpha: int) -> None:
    width, height = image.size
    fade_width = width - start_x
    mask_row = Image.new("L", (fade_width, 1))
    for x in range(fade_width):
        progress = x / max(1, fade_width - 1)
        alpha = int(maximum_alpha * (0.18 + 0.82 * progress))
        mask_row.putpixel((x, 0), alpha)
    mask = mask_row.resize((fade_width, height))
    panel = Image.new("RGBA", (fade_width, height), INK)
    panel.putalpha(mask)
    image.alpha_composite(panel, (start_x, 0))


def draw_rule(
    image: Image.Image,
    x0: int,
    x1: int,
    y: int,
    *,
    accent: tuple[int, int, int, int] = GOLD,
) -> None:
    draw = ImageDraw.Draw(image)
    draw.line((x0, y + 2, x1, y + 2), fill=(0, 0, 0, 190), width=5)
    draw.line((x0, y, x1, y), fill=GOLD_DARK, width=4)
    draw.line((x0, y - 1, x1, y - 1), fill=accent, width=2)


def render_github(source: Image.Image, font_path: Path) -> Image.Image:
    image = cover_crop(source, (1983, 793), focus_y=0.43)
    add_text_panel(image, start_x=780, maximum_alpha=188)

    draw_display_text(
        image,
        font_path,
        "ROLFMOLEMAN",
        (930, 118, 1900, 300),
        maximum_size=154,
        stroke_width=4,
    )
    draw_rule(image, 1010, 1820, 334)
    draw_display_text(
        image,
        font_path,
        "PLATFORM ENGINEERING",
        (1000, 365, 1830, 448),
        maximum_size=64,
        stroke_width=2,
    )
    draw_display_text(
        image,
        font_path,
        "INFRASTRUCTURE AND AUTOMATION",
        (955, 468, 1870, 548),
        maximum_size=54,
        stroke_width=2,
    )
    draw_display_text(
        image,
        font_path,
        "DOWN AT THE BOTTOM OF THE MOLE HOLE",
        (980, 620, 1845, 687),
        maximum_size=39,
        fill=GOLD,
        stroke_width=2,
    )
    draw_rule(image, 1120, 1705, 594, accent=BLUE)
    return image


def render_justgiving(source: Image.Image, font_path: Path) -> Image.Image:
    image = cover_crop(source, (1000, 563), focus_y=0.50)
    add_text_panel(image, start_x=385, maximum_alpha=200)

    draw_display_text(
        image,
        font_path,
        "ROLFMOLEMAN",
        (500, 48, 950, 95),
        maximum_size=34,
        fill=GOLD,
        stroke_width=2,
    )
    draw_display_text(
        image,
        font_path,
        "90 MILES",
        (430, 112, 965, 218),
        maximum_size=92,
        stroke_width=3,
    )
    draw_display_text(
        image,
        font_path,
        "IN OCTOBER",
        (425, 225, 970, 317),
        maximum_size=78,
        stroke_width=3,
    )
    draw_rule(image, 495, 920, 345, accent=BLUE)
    draw_display_text(
        image,
        font_path,
        "FUNDRAISING FOR MIND",
        (450, 370, 950, 425),
        maximum_size=42,
        stroke_width=2,
    )
    draw_display_text(
        image,
        font_path,
        "EVERY MILE MATTERS",
        (500, 471, 925, 518),
        maximum_size=35,
        fill=GOLD,
        stroke_width=2,
    )
    return image


def save_png(image: Image.Image, path: Path) -> None:
    image.convert("RGB").save(path, format="PNG", optimize=True)


def main() -> None:
    args = parse_args()
    validate_font(args.font)
    if not args.source.is_file():
        raise SystemExit(f"Source artwork not found at {args.source}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(args.source) as source_file:
        source = source_file.convert("RGB")
        github = render_github(source, args.font)
        justgiving = render_justgiving(source, args.font)

    github_path = args.output_dir / "rolfmoleman-github.png"
    justgiving_path = args.output_dir / "rolfmoleman-justgiving-mind.png"
    save_png(github, github_path)
    save_png(justgiving, justgiving_path)

    print(f"Rendered {github_path} ({github.size[0]}x{github.size[1]})")
    print(
        f"Rendered {justgiving_path} "
        f"({justgiving.size[0]}x{justgiving.size[1]})"
    )


if __name__ == "__main__":
    main()
