from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps, ImageStat, UnidentifiedImageError

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
    second_text: str
    logo_path: Path
    font_path: Path | None
    second_font_path: Path | None
    position: str
    y_offset_pixels: int
    opacity: float
    adaptive_opacity_enabled: bool
    brightness_threshold: int
    bright_background_opacity: float
    brightness_sample_padding_ratio: float
    margin_ratio: float
    font_size_ratio: float
    logo_width_ratio: float
    text_color: tuple[int, int, int]
    second_text_color: tuple[int, int, int]
    second_font_size_ratio: float | None
    second_font_size_delta_pixels: int
    line_spacing_ratio: float
    second_line_width_scale: float
    second_line_x_offset_pixels: int
    second_line_y_offset_pixels: int
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


def default_second_font_path() -> str:
    if watermark_settings.SECOND_FONT_PATH:
        return str(project_path(watermark_settings.SECOND_FONT_PATH))
    return watermark_settings.SECOND_FONT_NAME or default_font_path()


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
    parser.add_argument(
        "--second-text",
        default=watermark_settings.SECOND_TEXT_WATERMARK,
        help="second line text for camera settings or device notes",
    )
    parser.add_argument("--logo", default=config.LOGO_PATH, help="logo image path for image watermark")
    parser.add_argument("--font", default=default_font_path(), help="font name in fonts/ or font file path")
    parser.add_argument(
        "--second-font",
        default=default_second_font_path(),
        help="second line font name in fonts/ or font file path",
    )
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
    parser.add_argument(
        "--no-adaptive-opacity",
        action="store_true",
        help="disable automatic opacity boost on bright backgrounds",
    )
    parser.add_argument(
        "--brightness-threshold",
        type=int,
        default=watermark_settings.BRIGHTNESS_THRESHOLD,
        help="average brightness threshold from 0 to 255 for opacity boost",
    )
    parser.add_argument(
        "--bright-background-opacity",
        type=parse_opacity,
        default=watermark_settings.BRIGHT_BACKGROUND_OPACITY,
        help="opacity used when the watermark background is too bright",
    )
    parser.add_argument(
        "--brightness-sample-padding-ratio",
        type=float,
        default=watermark_settings.BRIGHTNESS_SAMPLE_PADDING_RATIO,
        help="extra surrounding area sampled around the watermark",
    )
    parser.add_argument("--margin-ratio", type=float, default=watermark_settings.MARGIN_RATIO)
    parser.add_argument(
        "--y-offset-pixels",
        type=int,
        default=watermark_settings.Y_OFFSET_PIXELS,
        help="vertical offset in pixels; negative moves watermark up",
    )
    parser.add_argument("--font-size-ratio", type=float, default=watermark_settings.FONT_SIZE_RATIO)
    parser.add_argument(
        "--second-font-size-delta-pixels",
        type=int,
        default=watermark_settings.SECOND_FONT_SIZE_DELTA_PIXELS,
        help="second line font size reduction in pixels",
    )
    parser.add_argument(
        "--second-font-size-ratio",
        type=float,
        default=watermark_settings.SECOND_FONT_SIZE_RATIO,
        help="second line font size as a ratio of the first line; overrides delta when set",
    )
    parser.add_argument(
        "--line-spacing-ratio",
        type=float,
        default=watermark_settings.LINE_SPACING_RATIO,
        help="line spacing based on first line font size",
    )
    parser.add_argument(
        "--second-line-width-scale",
        type=float,
        default=watermark_settings.SECOND_LINE_WIDTH_SCALE,
        help="second line horizontal scale; 1.12 makes it 12 percent wider",
    )
    parser.add_argument(
        "--second-line-x-offset-pixels",
        type=int,
        default=watermark_settings.SECOND_LINE_X_OFFSET_PIXELS,
        help="second line horizontal offset in pixels; negative moves left",
    )
    parser.add_argument(
        "--second-line-y-offset-pixels",
        type=int,
        default=watermark_settings.SECOND_LINE_Y_OFFSET_PIXELS,
        help="second line vertical offset in pixels; negative moves up",
    )
    parser.add_argument("--logo-width-ratio", type=float, default=config.LOGO_WIDTH_RATIO)
    parser.add_argument(
        "--text-color",
        type=parse_color,
        default=parse_color(watermark_settings.TEXT_COLOR),
    )
    parser.add_argument(
        "--second-text-color",
        type=parse_color,
        default=parse_color(watermark_settings.SECOND_TEXT_COLOR),
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
    second_font_path = Path(args.second_font) if args.second_font else font_path
    return WatermarkOptions(
        input_dir=Path(args.input),
        output_dir=Path(args.output),
        watermark_type=args.type,
        text=args.text,
        second_text=args.second_text,
        logo_path=Path(args.logo),
        font_path=font_path,
        second_font_path=second_font_path,
        position=args.position,
        y_offset_pixels=args.y_offset_pixels,
        opacity=args.opacity,
        adaptive_opacity_enabled=not args.no_adaptive_opacity,
        brightness_threshold=args.brightness_threshold,
        bright_background_opacity=args.bright_background_opacity,
        brightness_sample_padding_ratio=args.brightness_sample_padding_ratio,
        margin_ratio=args.margin_ratio,
        font_size_ratio=args.font_size_ratio,
        logo_width_ratio=args.logo_width_ratio,
        text_color=args.text_color,
        second_text_color=args.second_text_color,
        second_font_size_ratio=args.second_font_size_ratio,
        second_font_size_delta_pixels=args.second_font_size_delta_pixels,
        line_spacing_ratio=args.line_spacing_ratio,
        second_line_width_scale=args.second_line_width_scale,
        second_line_x_offset_pixels=args.second_line_x_offset_pixels,
        second_line_y_offset_pixels=args.second_line_y_offset_pixels,
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


def average_region_brightness(
    image: Image.Image,
    box: tuple[int, int, int, int],
    padding_ratio: float,
) -> float:
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    padding = max(0, int(max(width, height) * padding_ratio))
    padded_box = (
        max(0, left - padding),
        max(0, top - padding),
        min(image.width, right + padding),
        min(image.height, bottom + padding),
    )
    region = image.crop(padded_box).convert("L")
    return float(ImageStat.Stat(region).mean[0])


def should_boost_opacity(
    image: Image.Image,
    watermark_box: tuple[int, int, int, int],
    options: WatermarkOptions,
) -> bool:
    if not options.adaptive_opacity_enabled:
        return False
    if options.opacity >= options.bright_background_opacity:
        return False

    brightness = average_region_brightness(
        image,
        watermark_box,
        options.brightness_sample_padding_ratio,
    )
    logging.debug("Watermark background brightness: %.1f", brightness)
    return brightness >= options.brightness_threshold


def make_text_watermark(base_size: tuple[int, int], options: WatermarkOptions) -> Image.Image:
    image_width, _ = base_size
    font_size = max(8, int(image_width * options.font_size_ratio))
    second_text = options.second_text.strip()
    if options.second_font_size_ratio is not None:
        second_font_size = max(6, int(font_size * options.second_font_size_ratio))
    else:
        second_font_size = max(6, font_size - max(1, options.second_font_size_delta_pixels))
    stroke_width = max(0, int(image_width * options.stroke_width_ratio))
    shadow_offset = max(0, int(image_width * options.shadow_offset_ratio))
    line_spacing = max(0, int(font_size * options.line_spacing_ratio)) if second_text else 0
    first_font = load_font(options.font_path, font_size)
    second_font = load_font(options.second_font_path or options.font_path, second_font_size)

    measure = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(measure)
    lines = [
        (options.text, first_font, options.text_color),
    ]
    if second_text:
        lines.append((second_text, second_font, options.second_text_color))

    rendered_lines = []
    for index, (text, font, color) in enumerate(lines):
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        padding = max(stroke_width * 2, shadow_offset)
        line_image = Image.new(
            "RGBA",
            (width + padding * 2 + shadow_offset, height + padding * 2 + shadow_offset),
            (0, 0, 0, 0),
        )
        line_draw = ImageDraw.Draw(line_image)
        text_x = padding - bbox[0]
        text_y = padding - bbox[1]
        if shadow_offset:
            line_draw.text(
                (text_x + shadow_offset, text_y + shadow_offset),
                text,
                font=font,
                fill=(0, 0, 0, int(255 * options.opacity * 0.65)),
                stroke_width=stroke_width,
                stroke_fill=(0, 0, 0, int(255 * options.opacity * 0.55)),
            )
        line_draw.text(
            (text_x, text_y),
            text,
            font=font,
            fill=(*color, int(255 * options.opacity)),
            stroke_width=stroke_width,
            stroke_fill=(0, 0, 0, int(255 * options.opacity * 0.45)),
        )

        if index == 1 and options.second_line_width_scale > 0:
            scaled_width = max(1, int(line_image.width * options.second_line_width_scale))
            if scaled_width != line_image.width:
                line_image = line_image.resize(
                    (scaled_width, line_image.height),
                    Image.Resampling.LANCZOS,
                )

        rendered_lines.append(
            {
                "index": index,
                "image": line_image,
                "width": line_image.width,
                "height": line_image.height,
            }
        )

    second_x_extra = abs(options.second_line_x_offset_pixels) * 2 if second_text else 0
    top_extra = max(0, -options.second_line_y_offset_pixels) if second_text else 0
    bottom_extra = max(0, options.second_line_y_offset_pixels) if second_text else 0
    text_width = max(line["width"] for line in rendered_lines) + second_x_extra
    text_height = (
        sum(line["height"] for line in rendered_lines)
        + line_spacing * (len(rendered_lines) - 1)
        + top_extra
        + bottom_extra
    )

    watermark = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
    y = top_extra
    for line in rendered_lines:
        text_x = (text_width - line["width"]) // 2
        text_y = y
        if line["index"] == 1:
            text_x += options.second_line_x_offset_pixels
            text_y += options.second_line_y_offset_pixels
        watermark.alpha_composite(line["image"], (text_x, text_y))
        y += line["height"] + line_spacing
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

    y_offset_pixels = options.y_offset_pixels
    if options.watermark_type == "text" and options.second_text.strip():
        y_offset_pixels += watermark_settings.TWO_LINE_AUTO_Y_OFFSET_PIXELS

    x, y = watermark_position(
        base.size,
        watermark.size,
        options.position,
        margin,
        y_offset_pixels,
    )

    watermark_box = (x, y, x + watermark.width, y + watermark.height)
    if should_boost_opacity(base, watermark_box, options):
        boosted_opacity = max(options.opacity, options.bright_background_opacity)
        logging.info(
            "Bright watermark area detected; opacity boosted from %.2f to %.2f.",
            options.opacity,
            boosted_opacity,
        )
        boosted_options = replace(options, opacity=boosted_opacity)
        if boosted_options.watermark_type == "text":
            watermark = make_text_watermark(base.size, boosted_options)
        else:
            watermark = make_logo_watermark(base.size, boosted_options)
        x, y = watermark_position(
            base.size,
            watermark.size,
            boosted_options.position,
            margin,
            y_offset_pixels,
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
