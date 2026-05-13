# Photo Watermark

一个按方案实现的摄影作品批量加水印 Python 项目，支持文字水印和透明 PNG Logo 水印。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

当前机器如果已经安装 Pillow，也可以直接运行。

## 目录

```text
.
├── watermark.py
├── config.py
├── watermark_settings.py
├── run_text_watermark.command
├── run_text_watermark.sh
├── input/
├── fonts/
├── assets/
└── output/
```

把待处理照片放入 `input/`。文字水印参数在 `watermark_settings.py` 中修改。艺术字体可以放到 `fonts/` 目录，再通过 `FONT_NAME` 调用。如果使用图片水印，把透明背景 Logo 放到 `assets/logo.png`。

## 一键文字水印

macOS 可以双击运行：

```text
run_text_watermark.command
```

也可以双击启动图形界面应用：

```text
Photo Watermark.app
```

图形界面支持输入/输出目录选择、预览图选择、主/副水印文字、字体、字号、透明度、位置、第二行拉宽、第二行偏移和浅色背景自动增强透明度。点击 `Refresh Preview` 可以查看当前配置效果，点击 `Generate Watermarks` 批量生成，点击 `Save Settings` 会把界面中的水印参数保存回 `watermark_settings.py`。

终端中可以运行：

```bash
./run_text_watermark.sh
```

这两个启动文件都会读取 `watermark_settings.py`，并对 `input/` 中的照片生成文字水印，输出到 `output/`。

## 修改文字水印参数

打开 `watermark_settings.py` 修改：

```python
TEXT_WATERMARK = "Kintsugi | Nikon Zf"
SECOND_TEXT_WATERMARK = "Nikon Zf | NIKKOR Z 40mm f/2"
FONT_NAME = "SnellRoundhand.ttc"
SECOND_FONT_NAME = ""
FONT_SIZE_RATIO = 0.028
SECOND_FONT_SIZE_RATIO = None
SECOND_FONT_SIZE_DELTA_PIXELS = 2
LINE_SPACING_RATIO = 0.12
SECOND_LINE_WIDTH_SCALE = 1.12
SECOND_LINE_X_OFFSET_PIXELS = 0
SECOND_LINE_Y_OFFSET_PIXELS = 0
POSITION = "bottom_center"
Y_OFFSET_PIXELS = -40
TWO_LINE_AUTO_Y_OFFSET_PIXELS = -24
OPACITY = 0.45
ADAPTIVE_OPACITY_ENABLED = True
BRIGHTNESS_THRESHOLD = 185
BRIGHT_BACKGROUND_OPACITY = 0.98
BRIGHTNESS_SAMPLE_PADDING_RATIO = 0.35
```

如果 `SECOND_TEXT_WATERMARK` 为空字符串，则只生成单行签名：

```python
SECOND_TEXT_WATERMARK = ""
```

如果要给第二行单独指定字体，把字体文件放进 `fonts/`，然后设置：

```python
SECOND_FONT_NAME = "YourSmallTextFont.ttf"
```

如果要给第二行单独指定大小，可以设置：

```python
SECOND_FONT_SIZE_RATIO = 0.5
```

`SECOND_FONT_SIZE_RATIO` 是相对第一行字号的倍数，例如 `0.5` 表示第二行字号是第一行的 0.5 倍。如果 `SECOND_FONT_SIZE_RATIO = None`，则使用 `SECOND_FONT_SIZE_DELTA_PIXELS`，让第二行比第一行小几个像素。

如果要微调第二行相对第一行的位置：

```python
SECOND_LINE_WIDTH_SCALE = 1.12  # 1.12 表示第二行横向拉宽 12%
SECOND_LINE_X_OFFSET_PIXELS = 0   # 负数向左，正数向右
SECOND_LINE_Y_OFFSET_PIXELS = -4  # 负数向上，正数向下
```

字体查找顺序：

1. 如果设置了 `FONT_PATH`，优先使用它。
2. 否则从 `fonts/` 目录查找 `FONT_NAME`。
3. 如果没有找到，会尝试 macOS 常见艺术字体，如 Snell Roundhand、Brush Script、Zapfino。

## 文字水印

```bash
python3 watermark.py \
  --input ./input \
  --output ./output \
  --type text \
  --text "Kintsugi | Nikon Zf" \
  --position bottom_center \
  --opacity 0.9
```

## 图片水印

```bash
python3 watermark.py \
  --input ./input \
  --output ./output \
  --type image \
  --logo ./assets/logo.png \
  --position bottom_center \
  --opacity 0.5
```

## 常用参数

- `--recursive`：递归处理子文件夹。
- `--position`：`top_left`、`top_center`、`top_right`、`bottom_left`、`bottom_center`、`bottom_right`、`center`。
- `--y-offset-pixels -40`：垂直微调水印位置，负数向上，正数向下。
- `--second-text "Nikon Zf | ISO 100"`：添加第二行备注；为空时只生成单行水印。
- `--second-font MyNoteFont.ttf`：指定第二行字体。
- `--second-font-size-ratio 0.5`：指定第二行字号相对第一行的倍数。
- `--second-font-size-delta-pixels 2`：第二行比第一行小的像素数。
- `--second-line-width-scale 1.12`：第二行横向拉宽比例。
- `--second-line-x-offset-pixels 0`：第二行相对默认居中位置的左右偏移。
- `--second-line-y-offset-pixels -4`：第二行相对默认位置的上下偏移。
- `--opacity`：透明度，范围 `0` 到 `1`，摄影作品推荐 `0.35` 到 `0.60`。
- `--no-adaptive-opacity`：关闭浅色背景自动增强透明度。
- `--brightness-threshold 185`：背景平均亮度超过该值时增强水印，范围 `0` 到 `255`。
- `--bright-background-opacity 0.98`：浅色背景下使用的水印透明度。
- `--brightness-sample-padding-ratio 0.35`：检测水印周围区域时额外外扩的比例。
- `--font MySignature.ttf`：指定文字水印字体。可以写 `fonts/` 中的字体文件名，也可以写完整路径。
- `--font-size-ratio 0.035`：文字大小为图片宽度的比例。
- `--logo-width-ratio 0.12`：Logo 宽度为图片宽度的比例。
- `--jpeg-quality 95`：JPEG 输出质量。
- `--overwrite`：允许输出文件覆盖已有文件。
- `--no-exif`：不保留 EXIF。

默认不会覆盖原图，输出文件会添加 `_watermarked` 后缀。
