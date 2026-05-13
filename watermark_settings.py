"""Text watermark settings.

Edit this file when you want to change the visible watermark style.
Fonts are resolved from FONT_DIR first, so you can put artistic fonts in
the fonts/ directory and set FONT_NAME to that file name.
"""

TEXT_WATERMARK = "Kintsugi"
SECOND_TEXT_WATERMARK = "Shot by Nikon F2"

# Put .ttf, .otf, or .ttc font files in this directory.
FONT_DIR = "fonts"

# If this is set, it wins. It can be an absolute path or a path relative to this project.
FONT_PATH = ""

# If FONT_PATH is empty, the program looks for this file in FONT_DIR, then common system fonts.
FONT_NAME = "Corinthia-Regular.ttf"

# Leave empty to use the same font as the first line.
SECOND_FONT_PATH = ""
SECOND_FONT_NAME = "Ephesis-Regular.ttf"

FONT_SIZE_RATIO = 0.028
# Set to None to use SECOND_FONT_SIZE_DELTA_PIXELS instead.
# Example: 0.5 means the second line font size is half of the first line.
SECOND_FONT_SIZE_RATIO = 0.45
SECOND_FONT_SIZE_DELTA_PIXELS = 2
LINE_SPACING_RATIO = 0.12
SECOND_LINE_WIDTH_SCALE = 1.4
SECOND_LINE_X_OFFSET_PIXELS = 0
SECOND_LINE_Y_OFFSET_PIXELS = 0
TEXT_COLOR = "#FFFFFF"
SECOND_TEXT_COLOR = "#FFFFFF"
STROKE_WIDTH_RATIO = 0
SHADOW_OFFSET_RATIO = 0

POSITION = "bottom_center"
MARGIN_RATIO =0 #0.03
Y_OFFSET_PIXELS = -60
TWO_LINE_AUTO_Y_OFFSET_PIXELS = -24
OPACITY = 0.9
ADAPTIVE_OPACITY_ENABLED = True
BRIGHTNESS_THRESHOLD = 185
BRIGHT_BACKGROUND_OPACITY = 0.98
BRIGHTNESS_SAMPLE_PADDING_RATIO = 0.35
