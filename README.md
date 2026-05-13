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

终端中可以运行：

```bash
./run_text_watermark.sh
```

这两个启动文件都会读取 `watermark_settings.py`，并对 `input/` 中的照片生成文字水印，输出到 `output/`。

## 修改文字水印参数

打开 `watermark_settings.py` 修改：

```python
TEXT_WATERMARK = "Kintsugi | Nikon Zf"
FONT_NAME = "SnellRoundhand.ttc"
FONT_SIZE_RATIO = 0.028
POSITION = "bottom_center"
Y_OFFSET_PIXELS = -40
OPACITY = 0.45
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
- `--opacity`：透明度，范围 `0` 到 `1`，摄影作品推荐 `0.35` 到 `0.60`。
- `--font MySignature.ttf`：指定文字水印字体。可以写 `fonts/` 中的字体文件名，也可以写完整路径。
- `--font-size-ratio 0.035`：文字大小为图片宽度的比例。
- `--logo-width-ratio 0.12`：Logo 宽度为图片宽度的比例。
- `--jpeg-quality 95`：JPEG 输出质量。
- `--overwrite`：允许输出文件覆盖已有文件。
- `--no-exif`：不保留 EXIF。

默认不会覆盖原图，输出文件会添加 `_watermarked` 后缀。
