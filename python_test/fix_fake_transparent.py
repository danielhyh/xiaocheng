"""
棋盘格/白底假透明 → 真透明 PNG 转换工具
==========================================
专门处理 AI 生成的"假透明"素材图（棋盘格被烤进像素的情况）。
特别适合：发光线框、UI 边框、图标等高饱和度素材。

原理：用 HSV 色彩空间的饱和度(Saturation)区分前景和背景
  - 棋盘格/白底 = 无彩色(低饱和度) → 透明
  - 彩色线框/图标 = 有彩色(高饱和度) → 保留

用法：
  python fix_fake_transparent.py <图片路径> [输出路径]
  python fix_fake_transparent.py input.png                    # 输出 input_fixed.png
  python fix_fake_transparent.py input.png output.png         # 指定输出路径
  python fix_fake_transparent.py folder/                      # 批量处理整个目录

依赖：
  pip install opencv-python numpy
"""

import cv2
import numpy as np
from pathlib import Path
import sys


# ============================================================
# 可调参数
# ============================================================
SAT_THRESHOLD = 15      # 饱和度低于此值的像素视为背景（0-255）
                        # 增大 → 去除更多，可能误伤淡色元素
                        # 减小 → 保留更多，可能残留棋盘格痕迹

VAL_THRESHOLD = 150     # 亮度高于此值 + 低饱和度 = 棋盘格背景
                        # 降低 → 更激进去除浅色区域

ALPHA_SCALE = 4.0       # alpha 增益系数，控制线框的不透明度
                        # 增大 → 线框更实，减小 → 线框更虚

GLOW_PRESERVE = True    # 是否保留发光效果的渐变边缘
                        # True  → 线框边缘有柔和发光过渡
                        # False → 线框边缘硬切，更锐利


def load_image(path: str):
    """加载图片（支持中文路径）"""
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"无法加载: {path}")
    return img


def save_image(img, path: str):
    """保存图片（支持中文路径）"""
    ext = Path(path).suffix
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(str(path))


def fix_fake_transparent(img):
    """
    将假透明图（棋盘格/白底）转为真透明 PNG

    输入: BGR 或 BGRA 图像（numpy array）
    输出: BGRA 图像，背景区域 alpha=0
    """
    # 统一为 BGR
    if img.ndim == 3 and img.shape[2] == 4:
        bgr = img[:, :, :3]
    elif img.ndim == 3 and img.shape[2] == 3:
        bgr = img
    else:
        raise ValueError(f"不支持的图像格式: shape={img.shape}")

    # 转 HSV
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    sat = hsv[:, :, 1]   # 饱和度：0=无彩色(灰/白/黑)，255=纯色
    val = hsv[:, :, 2]   # 亮度

    # === 生成 alpha 通道 ===

    # 1. 棋盘格/白底区域：低饱和度 + 高亮度 → 完全透明
    is_background = (sat < SAT_THRESHOLD) & (val > VAL_THRESHOLD)

    # 2. 纯黑区域也视为背景（某些图的棋盘格有黑色块）
    brightness = bgr.astype(np.float32).mean(axis=2)
    is_dark_bg = (sat < SAT_THRESHOLD) & (brightness < 30)

    # 3. 前景区域：按饱和度生成 alpha
    if GLOW_PRESERVE:
        # 保留发光渐变：饱和度映射到 alpha，带平滑过渡
        alpha = np.clip(sat * ALPHA_SCALE, 0, 255)
    else:
        # 硬切：超过阈值就完全不透明
        alpha = np.where(sat > SAT_THRESHOLD * 2, 255, 0).astype(np.float32)

    # 4. 强制背景区域透明
    alpha[is_background] = 0
    alpha[is_dark_bg] = 0

    alpha = alpha.astype(np.uint8)

    # === 合成 BGRA ===
    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha

    return bgra


def process_file(input_path: Path, output_path: Path = None):
    """处理单个文件"""
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_fixed.png"

    img = load_image(str(input_path))
    h, w = img.shape[:2]
    channels = img.shape[2] if img.ndim == 3 else 1

    print(f"  输入: {input_path.name} ({w}×{h}, {channels}ch)")

    result = fix_fake_transparent(img)

    alpha = result[:, :, 3]
    transparent_pct = (alpha == 0).sum() / alpha.size * 100
    print(f"  输出: {output_path.name} (透明区域: {transparent_pct:.1f}%)")

    save_image(result, str(output_path))
    return output_path


def main():
    if len(sys.argv) < 2:
        print("用法: python fix_fake_transparent.py <图片或目录> [输出路径]")
        print()
        print("示例:")
        print("  python fix_fake_transparent.py border.png")
        print("  python fix_fake_transparent.py border.png border_out.png")
        print("  python fix_fake_transparent.py ./my_sprites/")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_arg = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if input_path.is_dir():
        # 批量模式
        exts = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}
        files = [f for f in input_path.iterdir() if f.suffix.lower() in exts]
        if not files:
            print(f"目录中没有找到图片: {input_path}")
            sys.exit(1)

        out_dir = output_arg or (input_path / "fixed")
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"批量处理 {len(files)} 个文件 → {out_dir}/")
        for f in sorted(files):
            out = out_dir / f"{f.stem}_fixed.png"
            process_file(f, out)

    elif input_path.is_file():
        # 单文件模式
        output_path = output_arg if output_arg else None
        process_file(input_path, output_path)

    else:
        print(f"路径不存在: {input_path}")
        sys.exit(1)

    print("\n✅ 完成!")
    print()
    print("💡 效果不理想？调整脚本顶部的参数：")
    print(f"  SAT_THRESHOLD = {SAT_THRESHOLD}   # 增大→去除更多背景")
    print(f"  ALPHA_SCALE = {ALPHA_SCALE}     # 增大→线框更实")
    print(f"  GLOW_PRESERVE = {GLOW_PRESERVE}  # False→硬边缘，更锐利")


if __name__ == "__main__":
    main()
