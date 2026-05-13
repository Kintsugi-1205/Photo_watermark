"""Text watermark settings.

Edit this file when you want to change the visible watermark style.
Fonts are resolved from FONT_DIR first, so you can put artistic fonts in
the fonts/ directory and set FONT_NAME to that file name.
"""

TEXT_WATERMARK = "Kintsugi @ Nikon Zf"

# Put .ttf, .otf, or .ttc font files in this directory.
FONT_DIR = "fonts"

# If this is set, it wins. It can be an absolute path or a path relative to this project.
FONT_PATH = ""

# If FONT_PATH is empty, the program looks for this file in FONT_DIR, then common system fonts.
FONT_NAME = "MrsSaintDelafield-Regular.ttf"

FONT_SIZE_RATIO = 0.028
TEXT_COLOR = "#FFFFFF"
STROKE_WIDTH_RATIO = 0
SHADOW_OFFSET_RATIO = 0

POSITION = "bottom_center"
MARGIN_RATIO =0 #0.03
Y_OFFSET_PIXELS = -60
OPACITY = 0.9
