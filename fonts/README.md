# Font Library

把艺术字体文件放到这个目录，例如：

- `MySignature.ttf`
- `MyCalligraphy.otf`
- `SnellRoundhand.ttc`

然后在项目根目录的 `watermark_settings.py` 中设置：

```python
FONT_NAME = "MySignature.ttf"
```

如果字体文件不在 `fonts/` 目录，也可以直接设置完整路径：

```python
FONT_PATH = "/path/to/font.ttf"
```
