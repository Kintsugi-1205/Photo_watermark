"""Project-level defaults for the photo watermark command line tool."""

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")

INPUT_DIR = "input"
OUTPUT_DIR = "output"
RECURSIVE = False
OVERWRITE = False
OUTPUT_SUFFIX = "_watermarked"

WATERMARK_TYPE = "text"

LOGO_PATH = "assets/logo.png"
LOGO_WIDTH_RATIO = 0.12

JPEG_QUALITY = 95
WEBP_QUALITY = 95
PRESERVE_EXIF = True

# Camera originals can exceed Pillow's conservative pixel warning threshold.
# Set to None to allow high-resolution local photography files.
IMAGE_PIXEL_LIMIT = None
