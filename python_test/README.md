# fix_panel_borders.py

`fix_panel_borders.py` 是一个面板边框素材透明化工具，用于把带黑底或白底的 `panel-frame-border` 图片处理成带 alpha 通道的 PNG。

## 作用

- `dark`：适合黑色/深色背景素材，按像素亮度生成透明度，黑色背景会变透明。
- `dark2`：黑底增强模式，对灰色过渡边缘处理更干净。
- `light`：适合白色/浅色背景素材，按像素与白色的色差生成透明度，白色背景会变透明。

## 依赖

需要 Python 环境中安装：

```bash
pip install opencv-python numpy
```

项目内运行 Python 命令时请先进入 `.venv` 虚拟环境。

## 用法

```bash
python fix_panel_borders.py border1.png --mode dark
python fix_panel_borders.py border1.png --mode dark2
python fix_panel_borders.py border4.png --mode light
```

默认输出到原文件同目录，文件名为：

```text
原文件名_fixed.png
```

也可以指定输出路径：

```bash
python fix_panel_borders.py border1.png --mode dark -o border1_fixed.png
```

## 常用参数

- `--threshold`：背景阈值。调大可以去掉更多背景杂色，但可能吃掉暗色边框细节。
- `--boost`：alpha 增益。调大可以让边框更实、更不透明。
- `--mode`：处理模式，可选 `dark`、`dark2`、`light`。

## 示例

黑底素材如果边缘有灰色残留，可以尝试：

```bash
python fix_panel_borders.py border1.png --mode dark2 --threshold 25 --boost 1.8
```

白底素材如果背景没有去干净，可以尝试：

```bash
python fix_panel_borders.py border4.png --mode light --threshold 40 --boost 2.0
```
