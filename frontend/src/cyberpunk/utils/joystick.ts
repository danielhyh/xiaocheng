/**
 * joystick.ts — 摇杆归一化工具
 *
 * 对应 PBT 属性 P1:
 *   对任意指针偏移 (dx, dy) ∈ ℝ² 与外圆半径 R > 0,
 *   clampToUnitDisk(dx/R, dy/R) 的结果向量 (u, v) 必须满足
 *       u² + v² ≤ 1 + 1e-6
 *   且当 |(dx, dy)| ≤ R 时有 (u, v) = (dx/R, dy/R) (线性区等价)。
 */

export interface Vec2 {
  x: number
  y: number
}

const EPSILON = 1e-6

/**
 * 将任意二维向量裁剪到单位圆盘内。
 *
 * 线性区 (|v| ≤ 1): 原样返回
 * 饱和区 (|v| > 1): 按长度重投影到单位圆周
 * 对 NaN / Infinity 输入返回 (0, 0)
 */
export function clampToUnitDisk(x: number, y: number): Vec2 {
  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    return { x: 0, y: 0 }
  }

  const mag2 = x * x + y * y
  if (mag2 <= 1) {
    return { x, y }
  }

  const mag = Math.sqrt(mag2)
  // 留出 epsilon 余量,避免后续比较浮点越界
  const scale = (1 - EPSILON) / mag
  return { x: x * scale, y: y * scale }
}

/**
 * 从指针事件相对于外圆圆心的偏移,计算归一化向量。
 * 这是摇杆组件的唯一归一化入口。
 */
export function normalizeOffset(dx: number, dy: number, radius: number): Vec2 {
  if (!Number.isFinite(radius) || radius <= 0) {
    return { x: 0, y: 0 }
  }
  return clampToUnitDisk(dx / radius, dy / radius)
}

/**
 * 数值小幅抖动过滤。
 * 摇杆拇指短暂回中时,认为输出就是 (0, 0)。
 */
export function quantize(v: number, step = 0.01): number {
  return Math.round(v / step) * step
}
