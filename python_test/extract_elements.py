"""
UI 素材切割工具
===============
从 sprite sheet / 设计稿中切出单个 UI 元素，输出透明背景 PNG。

两种模式：
  1. 自动模式（默认）：OpenCV 轮廓检测，适合元素间距均匀的图
  2. 手动模式：在 MANUAL_REGIONS 中定义坐标，精确控制每个切割区域

用法：
  python extract_elements.py <图片路径> [输出目录]

依赖：
  pip install opencv-python numpy
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import json


# ============================================================
# 手动区域定义（当自动检测效果不佳时使用）
# 格式：{"输出文件名": [x, y, width, height]}
# 可以用画图/PS/截图工具量取像素坐标
# 取消注释并填入实际坐标即可启用手动模式
# ============================================================
MANUAL_REGIONS = None  # 设为 None 使用自动模式

# 示例（取消注释后修改坐标）：
# MANUAL_REGIONS = {
#     "bg_fpv_environment":    [18,  42, 450, 330],
#     "hud_topbar_bg":         [490, 42, 590,  55],
#     "btn_gimbal_default":    [1130, 55,  90,  90],
#     "btn_gimbal_active":     [1290, 55,  90,  90],
#     "joystick_drive":        [100, 420, 160, 160],
#     "icon_battery":          [720, 440,  55,  55],
# }


# ============================================================
# 可调参数
# ============================================================
BRIGHTNESS_THRESHOLD = 22   # 亮度阈值（越低越灵敏，可能引入噪点）
MIN_AREA = 400              # 最小面积（像素²），过滤噪点
MERGE_DISTANCE = 8          # bbox 合并距离（像素），防止同一元素被拆成多块
BG_TOLERANCE = 35           # 背景去除容差（越大越激进）
CROP_PADDING = 4            # 裁剪时额外保留的边距


# ============================================================
# 核心函数
# ============================================================

def load_image(path: str):
    """加载图片（支持中文路径）"""
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"无法加载: {path}")
    if img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


def save_image(img, path: str):
    """保存图片（支持中文路径）"""
    ext = Path(path).suffix
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)


def find_bboxes_auto(img):
    """自动检测元素 bounding box"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, BRIGHTNESS_THRESHOLD, 255, cv2.THRESH_BINARY)

    # 轻度膨胀连接碎片，不要太激进以免合并不同元素
    k1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.dilate(binary, k1, iterations=2)
    k2 = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, k2, iterations=1)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bboxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w * h >= MIN_AREA and w > 10 and h > 10:
            bboxes.append([x, y, x + w, y + h])

    return _merge_bboxes(bboxes, MERGE_DISTANCE)


def _merge_bboxes(bboxes, dist):
    """合并距离过近的 bounding box"""
    if not bboxes:
        return []
    changed = True
    while changed:
        changed = False
        result, used = [], [False] * len(bboxes)
        for i in range(len(bboxes)):
            if used[i]:
                continue
            cur = list(bboxes[i])
            for j in range(i + 1, len(bboxes)):
                if used[j]:
                    continue
                b = bboxes[j]
                if (cur[0] - dist <= b[2] and cur[2] + dist >= b[0] and
                    cur[1] - dist <= b[3] and cur[3] + dist >= b[1]):
                    cur = [min(cur[0], b[0]), min(cur[1], b[1]),
                           max(cur[2], b[2]), max(cur[3], b[3])]
                    used[j] = True
                    changed = True
            result.append(cur)
            used[i] = True
        bboxes = result
    return bboxes


def remove_background(crop_bgr, tolerance=None):
    """
    去除裁剪区域的背景色，返回 BGRA 图像
    原理：采样边缘像素估计背景色，按颜色距离生成 alpha 通道
    """
    tol = tolerance or BG_TOLERANCE
    h, w = crop_bgr.shape[:2]
    sw = max(2, min(5, min(h, w) // 10))

    # 采样四条边的像素作为背景色参考
    edges = []
    if h > sw * 2 and w > sw * 2:
        edges.extend([
            crop_bgr[:sw, :].reshape(-1, 3),     # 上边
            crop_bgr[-sw:, :].reshape(-1, 3),     # 下边
            crop_bgr[:, :sw].reshape(-1, 3),      # 左边
            crop_bgr[:, -sw:].reshape(-1, 3),     # 右边
        ])

    if edges:
        samples = np.concatenate(edges, axis=0).astype(np.float32)
        bg = np.median(samples, axis=0)  # 中位数比均值更鲁棒
    else:
        bg = np.array([0, 0, 0], dtype=np.float32)

    # 计算每个像素到背景色的欧氏距离
    diff = crop_bgr.astype(np.float32) - bg
    dist = np.sqrt(np.sum(diff ** 2, axis=2))

    # 渐变 alpha（避免硬边缘锯齿）
    alpha = np.clip((dist - tol) / (tol * 0.5), 0, 1) * 255
    bgra = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha.astype(np.uint8)
    return bgra


def trim_alpha(bgra, padding=2):
    """裁掉全透明的边缘"""
    a = bgra[:, :, 3]
    rows, cols = np.any(a > 0, axis=1), np.any(a > 0, axis=0)
    if not rows.any() or not cols.any():
        return bgra
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    h, w = bgra.shape[:2]
    return bgra[max(0, r0 - padding):min(h, r1 + padding + 1),
                max(0, c0 - padding):min(w, c1 + padding + 1)]


def extract_one(img, name, x, y, w, h, output_dir, remove_bg=True):
    """裁剪 + 去背景 + 保存单个元素"""
    ih, iw = img.shape[:2]
    p = CROP_PADDING
    x0, y0 = max(0, x - p), max(0, y - p)
    x1, y1 = min(iw, x + w + p), min(ih, y + h + p)
    crop = img[y0:y1, x0:x1]

    if remove_bg:
        result = remove_background(crop)
        result = trim_alpha(result)
    else:
        # 不去背景，仅裁剪（适合背景图等）
        result = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)

    out_path = str(Path(output_dir) / f"{name}.png")
    save_image(result, out_path)
    return out_path


# ============================================================
# 主流程
# ============================================================

def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "input.png"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output_elements"

    print(f"加载图片: {input_path}")
    img = load_image(input_path)
    h, w = img.shape[:2]
    print(f"尺寸: {w} x {h}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if MANUAL_REGIONS:
        # ===== 手动模式 =====
        print(f"\n📐 手动模式：{len(MANUAL_REGIONS)} 个区域")
        for name, (rx, ry, rw, rh) in MANUAL_REGIONS.items():
            path = extract_one(img, name, rx, ry, rw, rh, output_dir)
            print(f"  ✓ {name} ({rw}×{rh})")

    else:
        # ===== 自动模式 =====
        bboxes = find_bboxes_auto(img)
        bboxes.sort(key=lambda b: (b[1] // 40, b[0]))
        print(f"\n🔍 自动检测到 {len(bboxes)} 个元素")

        # 预览图：在原图上画出检测框
        preview = img.copy()
        for i, (x1, y1, x2, y2) in enumerate(bboxes):
            cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(preview, str(i + 1), (x1 + 2, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        save_image(preview, str(out / "_detection_preview.png"))
        print(f"预览图: {out}/_detection_preview.png")

        # 导出坐标 JSON（方便后续微调后切换到手动模式）
        regions = {}
        for i, (x1, y1, x2, y2) in enumerate(bboxes):
            regions[f"element_{i+1:03d}"] = [x1, y1, x2 - x1, y2 - y1]
        json_path = str(out / "_regions.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(regions, f, indent=2, ensure_ascii=False)
        print(f"坐标文件: {json_path}")

        # 逐个切割保存
        for i, (x1, y1, x2, y2) in enumerate(bboxes):
            name = f"element_{i+1:03d}_{x2-x1}x{y2-y1}"
            extract_one(img, name, x1, y1, x2 - x1, y2 - y1, output_dir)

    total = len(MANUAL_REGIONS) if MANUAL_REGIONS else len(bboxes)
    print(f"\n✅ 完成！{total} 个元素已保存到: {output_dir}/")

    if not MANUAL_REGIONS:
        print()
        print("💡 自动检测不完美？两种改进方式：")
        print("   方式一 · 调参数：修改脚本顶部的常量")
        print(f"     BRIGHTNESS_THRESHOLD = {BRIGHTNESS_THRESHOLD}  (降低 → 检测更暗的元素)")
        print(f"     MIN_AREA = {MIN_AREA}  (降低 → 保留更小的元素)")
        print(f"     MERGE_DISTANCE = {MERGE_DISTANCE}  (增大 → 合并更远的碎片)")
        print(f"     BG_TOLERANCE = {BG_TOLERANCE}  (增大 → 去除更多背景残留)")
        print()
        print("   方式二 · 手动模式：")
        print(f"     1. 打开 {json_path} 查看自动检测的坐标")
        print("     2. 复制到脚本中的 MANUAL_REGIONS 字典")
        print("     3. 重命名 key、微调坐标，重新运行")


if __name__ == "__main__":
    main()
