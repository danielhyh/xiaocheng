/**
 * battery.ts — 电量档位映射
 *
 * 对应 PBT 属性 P3:
 *   mapBatteryLevel(level) → { text, tone, blink } 必须是确定性纯函数
 *   对任意不在 {ok, low, critical, unknown} 之外的输入必须回落到 "未知"
 *
 * 前端不引入任何电压阈值, 完全以后端 battery_level 字符串枚举为准。
 */

export type BatteryLevel = 'ok' | 'low' | 'critical' | 'unknown'

export type BatteryTone = 'green' | 'yellow' | 'red' | 'gray'

export interface BatteryView {
  text: '良好' | '偏低' | '危险' | '未知'
  tone: BatteryTone
  blink: boolean
}

const TABLE: Record<BatteryLevel, BatteryView> = {
  ok:       { text: '良好', tone: 'green',  blink: false },
  low:      { text: '偏低', tone: 'yellow', blink: false },
  critical: { text: '危险', tone: 'red',    blink: true  },
  unknown:  { text: '未知', tone: 'gray',   blink: false },
}

/**
 * 纯函数: 任何非法输入都会被规整为 "unknown"。
 */
export function mapBatteryLevel(level: unknown): BatteryView {
  if (typeof level === 'string' && level in TABLE) {
    return TABLE[level as BatteryLevel]
  }
  return TABLE.unknown
}

/**
 * 档位颜色 token. 用于 HUD / 动画共享配色。
 */
export const TONE_COLOR: Record<BatteryTone, string> = {
  green:  '#2dff88',
  yellow: '#ffd23a',
  red:    '#ff3a4a',
  gray:   '#8a96a6',
}
