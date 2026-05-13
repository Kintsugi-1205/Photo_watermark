from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

import config
import watermark_settings

Image.MAX_IMAGE_PIXELS = config.IMAGE_PIXEL_LIMIT


POSITIONS = (
    "top_left",
    "top_center",
    "top_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
    "center",
)


@dataclass(frozen=True)
class WatermarkOptions:
    input_dir: Path
    output_dir: Path
    watermark_type: str
    text: str
    logo_path: Path
    font_path: Path | None
    position: str
    y_offset_pixels: int
    opacity: float
    margin_ratio: float
    font_size_ratio: float
    logo_width_ratio: float
    text_color: tuple[int, int, int]
    stroke_width_ratio: float
    shadow_offset_ratio: float
    jpeg_quality: int
    webp_quality: int
    recursive: bool
    overwrite: bool
    suffix: str
    preserve_exif: bool


def project_path(path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parent / path


def default_font_path() -> str:
    if watermark_settings.FONT_PATH:
        return str(project_path(watermark_settings.FONT_PATH))
    return watermark_settings.FONT_NAME


def parse_color(value: str) -> tuple[int, int, int]:
    try:
        rgba = ImageColor.getcolor(value, "RGBA")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid color: {value}") from exc
    return rgba[:3]


def parse_opacity(value: str) -> float:
    try:
        opacity = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("opacity must be a number from 0 to 1") from exc
    if not 0 <= opacity <= 1:
        raise argparse.ArgumentTypeError("opacity must be between 0 and 1")
    return opacity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch add text or logo watermarks to photography images."
    )
    parser.add_argument("--input", default=config.INPUT_DIR, help="input image directory")
    parser.add_argument("--output", default=config.OUTPUT_DIR, help="output image directory")
    parser.add_argument(
        "--type",
        choices=("text", "image"),
        default=config.WATERMARK_TYPE,
        help="watermark type",
    )
    parser.add_argument("--text", default=watermark_settings.TEXT_WATERMARK, help="text watermark content")
    parser.add_argument("--logo", default=config.LOGO_PATH, help="logo image path for image watermark")
    parser.add_argument("--font", default=default_font_path(), help="font name in fonts/ or font file path")
    parser.add_argument(
        "--position",
        choices=POSITIONS,
        default=watermark_settings.POSITION,
        help="watermark position",
    )
    parser.add_argument(
        "--opacity",
        type=parse_opacity,
        default=watermark_settings.OPACITY,
        help="opacity from 0 to 1",
    )
    parser.add_argument("--margin-ratio", type=float, default=watermark_settings.MARGIN_RATIO)
    parser.add_argument(
        "--y-offset-pixels",
        type=int,
        default=watermark_settings.Y_OFFSET_PIXELS,
        help="vertical offset in pixels; negative moves watermark up",
    )
    parser.add_argument("--font-size-ratio", type=float, default=watermark_settings.FONT_SIZE_RATIO)
    parser.add_argument("--logo-width-ratio", type=float, default=config.LOGO_WIDTH_RATIO)
    parser.add_argument(
        "--text-color",
        type=parse_color,
        default=parse_color(watermark_settings.TEXT_COLOR),
    )
    parser.add_argument("--jpeg-quality", type=int, default=config.JPEG_QUALITY)
    parser.add_argument("--webp-quality", type=int, default=config.WEBP_QUALITY)
    parser.add_argument("--suffix", default=config.OUTPUT_SUFFIX, help="suffix added before extension")
    parser.add_argument("--recursive", action="store_true", default=config.RECURSIVE)
    parser.add_argument("--overwrite", action="store_true", default=config.OVERWRITE)
    parser.add_argument("--no-exif", action="store_true", help="do not preserve EXIF metadata")
    parser.add_argument("--verbose", action="store_true", help="show detailed processing logs")
    return parser


def options_from_args(args: argparse.Namespace) -> WatermarkOptions:
    font_path = Path(args.font) if args.font else None
    return WatermarkOptions(
        input_dir=Path(args.input),
        output_dir=Path(args.output),
        watermark_type=args.type,
        text=args.text,
        logo_path=Path(args.logo),
        font_path=font_path,
        position=args.position,
        y_offset_pixels=args.y_offset_pixels,
        opacity=args.opacity,
        margin_ratio=args.margin_ratio,
        font_size_ratio=args.font_size_ratio,
        logo_width_ratio=args.logo_width_ratio,
        text_color=args.text_color,
        stroke_width_ratio=watermark_settings.STROKE_WIDTH_RATIO,
        shadow_offset_ratio=watermark_settings.SHADOW_OFFSET_RATIO,
        jpeg_quality=args.jpeg_quality,
        webp_quality=args.webp_quality,
        recursive=args.recursive,
        overwrite=args.overwrite,
        suffix=args.suffix,
        preserve_exif=not args.no_exif,
    )


def iter_images(input_dir: Path, recursive: bool) -> Iterable[Path]:
    pattern = "**/*" if recursive else "*"
    for path in sorted(input_dir.glob(pattern)):
        if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            yield path


def load_font(font_path: Path | None, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path:
        font_candidates = []
        if font_path.is_absolute() or font_path.parent != Path("."):
            font_candidates.append(font_path)
        else:
            font_candidates.append(project_path(watermark_settings.FONT_DIR) / font_path.name)
            font_candidates.append(font_path)

        for candidate in font_candidates:
            if candidate.is_file():
                return ImageFont.truetype(str(candidate), font_size)

    candidates = (
        "/System/Library/Fonts/Supplemental/SnellRoundhand.ttc",
        "/System/Library/Fonts/Supplemental/Brush Script.ttf",
        "/System/Library/Fonts/Supplemental/Zapfino.ttf",
        "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/Library/Fonts/Arial.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, font_size)

    logging.warning("No configured font found; falling back to Pillow default font.")
    return ImageFont.load_default()


def apply_opacity(layer: Image.Image, opacity: float) -> Image.Image:
    rgba = layer.convert("RGBA")
    alpha = rgba.getchannel("A").point(lambda value: int(value * opacity))
    rgba.putalpha(alpha)
    return rgba


def watermark_position(
    image_size: tuple[int, int],
    watermark_size: tuple[int, int],
    position: str,
    margin: int,
    y_offset_pixels: int,
) -> tuple[int, int]:
    image_width, image_height = image_size
    watermark_width, watermark_height = watermark_size

    positions = {
        "top_left": (margin, margin),
        "top_center": ((image_width - watermark_width) // 2, margin),
        "top_right": (image_width - watermark_width - margin, margin),
        "bottom_left": (margin, image_height - watermark_height - margin),
        "bottom_center": ((image_width - watermark_width) // 2, image_height - watermark_height - margin),
        "bottom_right": (image_width - watermark_width - margin, image_height - watermark_height - margin),
        "center": ((image_width - watermark_width) // 2, (image_height - watermark_height) // 2),
    }

    if position not in positions:
        raise ValueError(f"unsupported position: {position}")

    x, y = positions[position]
    return x, max(0, min(image_height - watermark_height, y + y_offset_pixels))


def make_text_watermark(base_size: tuple[int, int], options: WatermarkOptions) -> Image.Image:
    image_width, _ = base_size
    font_size = max(8, int(image_width * options.font_size_ratio))
    stroke_width = max(1, int(image_width * options.stroke_width_ratio))
    shadow_offset = max(1, int(image_width * options.shadow_offset_ratio))
    font = load_font(options.font_path, font_size)

    measure = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(measure)
    bbox = draw.textbbox((0, 0), options.text, font=font, stroke_width=stroke_width)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = max(stroke_width * 2, shadow_offset)
    watermark = Image.new(
        "RGBA",
        (text_width + padding * 2 + shadow_offset, text_height + padding * 2 + shadow_offset),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(watermark)
    text_xy = (padding - bbox[0], padding - bbox[1])
    shadow_xy = (text_xy[0] + shadow_offset, text_xy[1] + shadow_offset)

    draw.text(
        shadow_xy,
        options.text,
        font=font,
        fill=(0, 0, 0, int(255 * options.opacity * 0.65)),
        stroke_width=stroke_width,
        stroke_fill=(0, 0, 0, int(255 * options.opacity * 0.55)),
    )
    draw.text(
        text_xy,
        options.text,
        font=font,
        fill=(*options.text_color, int(255 * options.opacity)),
        stroke_width=stroke_width,
        stroke_fill=(0, 0, 0, int(255 * options.opacity * 0.45)),
    )
    return watermark


def make_logo_watermark(base_size: tuple[int, int], options: WatermarkOptions) -> Image.Image:
    if not options.logo_path.is_file():
        raise FileNotFoundError(f"logo file not found: {options.logo_path}")

    logo = Image.open(options.logo_path).convert("RGBA")
    target_width = max(1, int(base_size[0] * options.logo_width_ratio))
    target_height = max(1, int(target_width * logo.height / logo.width))
    logo = logo.resize((target_width, target_height), Image.Resampling.LANCZOS)
    return apply_opacity(logo, options.opacity)


def add_watermark(image: Image.Image, options: WatermarkOptions) -> Image.Image:
    base = ImageOps.exif_transpose(image).convert("RGBA")
    margin = max(0, int(base.width * options.margin_ratio))

    if options.watermark_type == "text":
        watermark = make_text_watermark(base.size, options)
    else:
        watermark = make_logo_watermark(base.size, options)

    x, y = watermark_position(
        base.size,
        watermark.size,
        options.position,
        margin,
        options.y_offset_pixels,
    )
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.alpha_composite(watermark, (x, y))
    return Image.alpha_composite(base, layer)


def relative_output_path(source: Path, options: WatermarkOptions) -> Path:
    relative = source.relative_to(options.input_dir)
    stem = relative.stem if options.overwrite else f"{relative.stem}{options.suffix}"
    return options.output_dir / relative.with_name(f"{stem}{relative.suffix}")


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def save_image(
    image: Image.Image,
    source_image: Image.Image,
    output_path: Path,
    options: WatermarkOptions,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    save_kwargs: dict[str, object] = {}

    if options.preserve_exif and suffix in (".jpg", ".jpeg", ".tif", ".tiff", ".webp"):
        exif = source_image.getexif()
        if exif:
            exif.pop(0x0112, None)  # Orientation has already been applied by ImageOps.exif_transpose.
            save_kwargs["exif"] = exif.tobytes()

    if suffix in (".jpg", ".jpeg"):
        image = image.convert("RGB")
        save_kwargs.update(quality=options.jpeg_quality, subsampling=0, optimize=True)
    elif suffix == ".webp":
        save_kwargs.update(quality=options.webp_quality, method=6)
    elif suffix in (".tif", ".tiff"):
        save_kwargs.setdefault("compression", "tiff_deflate")

    image.save(output_path, **save_kwargs)


def process_one(source: Path, options: WatermarkOptions) -> Path:
    output_path = relative_output_path(source, options)
    if not options.overwrite:
        output_path = unique_path(output_path)

    with Image.open(source) as image:
        watermarked = add_watermark(image, options)
        save_image(watermarked, image, output_path, options)
    return output_path


def run(options: WatermarkOptions) -> int:
    if not options.input_dir.exists():
        raise FileNotFoundError(f"input directory not found: {options.input_dir}")
    if not options.input_dir.is_dir():
        raise NotADirectoryError(f"input path is not a directory: {options.input_dir}")

    options.output_dir.mkdir(parents=True, exist_ok=True)
    images = list(iter_images(options.input_dir, options.recursive))
    if not images:
        logging.warning("No supported images found in %s", options.input_dir)
        return 0

    success = 0
    failed: list[tuple[Path, str]] = []

    for index, source in enumerate(images, start=1):
        logging.info("[%d/%d] Processing %s", index, len(images), source)
        try:
            output_path = process_one(source, options)
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            failed.append((source, str(exc)))
            logging.error("Failed: %s (%s)", source, exc)
            continue
        success += 1
        logging.info("Saved: %s", output_path)

    logging.info("Done. %d succeeded, %d failed.", success, len(failed))
    if failed:
        logging.error("Failed files:")
        for source, reason in failed:
            logging.error("- %s: %s", source, reason)
        return 1
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    options = options_from_args(args)
    try:
        return run(options)
    except Exception as exc:
        logging.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
