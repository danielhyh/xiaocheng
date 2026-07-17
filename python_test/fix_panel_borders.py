"""
针对 panel-frame-border 素材的专用透明化脚本
==============================================
两种模式：
  - 黑底模式(border1): 线框是彩色/亮色，背景是黑/深灰 → 用亮度做 alpha
  - 白底模式(border4): 线框是彩色，背景是白/浅灰 → 用边缘+颜色差异做 alpha

原理：
  黑底: 越亮的像素越不透明（亮度直接映射 alpha），纯黑=全透明
  白底: 与纯白的色差越大越不透明，纯白=全透明

用法：
  python fix_panel_borders.py border1.png --mode dark
  python fix_panel_borders.py border4.png --mode light
  python fix_panel_borders.py border1.png --mode dark --threshold 20
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import argparse


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


def fix_dark_background(img, bg_threshold=30, alpha_boost=1.5):
    """
    黑底/深色底模式
    
    策略：用像素亮度(luminance)直接作为 alpha
    - 纯黑像素 → alpha=0（全透明）
    - 亮色线框 → alpha=255（不透明）
    - 中间灰色过渡 → 半透明（保留发光感）
    
    参数：
      bg_threshold: 亮度低于此值的像素直接设为全透明（去除深灰噪点）
      alpha_boost: alpha 增益，>1 让线框更实
    """
    if img.ndim == 3 and img.shape[2] == 4:
        bgr = img[:, :, :3]
    else:
        bgr = img

    # 计算亮度（加权灰度）
    # 用 max(R,G,B) 而不是平均值，这样彩色线框即使单通道亮也能保留
    bgr_f = bgr.astype(np.float32)
    luminance = np.max(bgr_f, axis=2)  # 取最亮通道

    # 生成 alpha：亮度映射
    # 低于阈值的直接透明，高于阈值的按比例映射
    alpha = np.zeros_like(luminance)
    mask = luminance > bg_threshold
    # 将 [bg_threshold, 255] 映射到 [0, 255]
    alpha[mask] = ((luminance[mask] - bg_threshold) / (255.0 - bg_threshold)) * 255.0
    
    # 增益
    alpha = np.clip(alpha * alpha_boost, 0, 255).astype(np.uint8)

    # 合成 BGRA
    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha

    return bgra


def fix_light_background(img, bg_threshold=30, alpha_boost=2.0):
    """
    白底/浅色底模式
    
    策略：计算每个像素与纯白(255,255,255)的色差，色差越大越不透明
    - 纯白像素 → alpha=0（全透明）
    - 彩色线框 → alpha=255（不透明）
    
    参数：
      bg_threshold: 与白色的色差低于此值的像素直接设为全透明
      alpha_boost: alpha 增益
    """
    if img.ndim == 3 and img.shape[2] == 4:
        bgr = img[:, :, :3]
    else:
        bgr = img

    bgr_f = bgr.astype(np.float32)
    
    # 计算与纯白的欧氏距离（色差）
    # 纯白 = (255, 255, 255)，距离越远说明越不是背景
    white = np.array([255.0, 255.0, 255.0])
    diff = np.sqrt(np.sum((bgr_f - white) ** 2, axis=2))
    # 最大可能距离 = sqrt(255^2 * 3) ≈ 441.67
    max_diff = np.sqrt(255.0**2 * 3)
    
    # 归一化到 [0, 255]
    alpha = (diff / max_diff) * 255.0
    
    # 低于阈值的直接透明
    alpha[alpha < bg_threshold] = 0
    
    # 重新映射 [bg_threshold, 255] → [0, 255] 并增益
    mask = alpha >= bg_threshold
    alpha[mask] = ((alpha[mask] - bg_threshold) / (255.0 - bg_threshold)) * 255.0
    alpha = np.clip(alpha * alpha_boost, 0, 255).astype(np.uint8)

    # 合成 BGRA
    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha

    return bgra


def fix_dark_v2(img, bg_threshold=25, mid_threshold=80, alpha_boost=1.8):
    """
    黑底模式 v2 - 更干净的版本
    
    三段式处理：
    - 亮度 < bg_threshold → 全透明（黑色背景）
    - bg_threshold < 亮度 < mid_threshold → 快速过渡（消除灰色糊边）
    - 亮度 > mid_threshold → 接近不透明（线框主体）
    """
    if img.ndim == 3 and img.shape[2] == 4:
        bgr = img[:, :, :3]
    else:
        bgr = img

    bgr_f = bgr.astype(np.float32)
    luminance = np.max(bgr_f, axis=2)

    alpha = np.zeros_like(luminance)
    
    # 中间过渡区：用 sigmoid 风格的快速过渡
    mid_mask = (luminance > bg_threshold) & (luminance <= mid_threshold)
    high_mask = luminance > mid_threshold
    
    # 过渡区：非线性映射，让灰色区域快速变透明
    t = (luminance[mid_mask] - bg_threshold) / (mid_threshold - bg_threshold)
    alpha[mid_mask] = (t ** 2) * 128  # 二次曲线，前半段压低
    
    # 高亮区：线性映射到 [128, 255]
    t2 = (luminance[high_mask] - mid_threshold) / (255.0 - mid_threshold)
    alpha[high_mask] = 128 + t2 * 127
    
    # 增益
    alpha = np.clip(alpha * alpha_boost, 0, 255).astype(np.uint8)

    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha

    return bgra


def main():
    parser = argparse.ArgumentParser(description='Panel frame border 透明化工具')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('--mode', choices=['dark', 'light', 'dark2'], default='dark',
                        help='dark=黑底, light=白底, dark2=黑底v2(更干净)')
    parser.add_argument('--threshold', type=int, default=None,
                        help='背景阈值 (dark默认25, light默认30)')
    parser.add_argument('--boost', type=float, default=None,
                        help='alpha增益 (dark默认1.5, light默认2.0)')
    parser.add_argument('--output', '-o', help='输出路径（默认在原文件名后加_fixed）')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"文件不存在: {input_path}")
        sys.exit(1)
    
    output_path = Path(args.output) if args.output else \
                  input_path.parent / f"{input_path.stem}_fixed.png"
    
    img = load_image(str(input_path))
    h, w = img.shape[:2]
    channels = img.shape[2] if img.ndim == 3 else 1
    print(f"输入: {input_path.name} ({w}×{h}, {channels}ch)")
    print(f"模式: {args.mode}")
    
    if args.mode == 'dark':
        threshold = args.threshold if args.threshold is not None else 25
        boost = args.boost if args.boost is not None else 1.5
        result = fix_dark_background(img, bg_threshold=threshold, alpha_boost=boost)
        print(f"参数: bg_threshold={threshold}, alpha_boost={boost}")
        
    elif args.mode == 'dark2':
        threshold = args.threshold if args.threshold is not None else 25
        boost = args.boost if args.boost is not None else 1.8
        result = fix_dark_v2(img, bg_threshold=threshold, alpha_boost=boost)
        print(f"参数: bg_threshold={threshold}, alpha_boost={boost}")
        
    elif args.mode == 'light':
        threshold = args.threshold if args.threshold is not None else 30
        boost = args.boost if args.boost is not None else 2.0
        result = fix_light_background(img, bg_threshold=threshold, alpha_boost=boost)
        print(f"参数: bg_threshold={threshold}, alpha_boost={boost}")
    
    # 统计
    alpha = result[:, :, 3]
    transparent_pct = (alpha == 0).sum() / alpha.size * 100
    opaque_pct = (alpha == 255).sum() / alpha.size * 100
    semi_pct = 100 - transparent_pct - opaque_pct
    
    print(f"\n输出: {output_path.name}")
    print(f"  全透明: {transparent_pct:.1f}%")
    print(f"  半透明: {semi_pct:.1f}%")
    print(f"  不透明: {opaque_pct:.1f}%")
    
    save_image(result, str(output_path))
    print("\n✅ 完成!")
    print()
    print("💡 调参建议：")
    print("  --threshold 增大 → 去除更多背景（但可能吃掉暗色线框）")
    print("  --boost 增大 → 线框更实/不透明")
    print("  --mode dark2 → 黑底专用，灰色过渡区更干净")


if __name__ == "__main__":
    main()
