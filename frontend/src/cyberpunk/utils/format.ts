/**
 * format.ts — 显示格式化工具
 *
 * 约束 (R17.4): 后端字段为 null/undefined 时必须显示占位符 "--" 而非崩溃。
 */

const DASH = '--'

export function fmtNum(
  v: number | null | undefined,
  fractionDigits = 0,
  fallback = DASH,
): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return fallback
  return v.toFixed(fractionDigits)
}

export function fmtInt(v: number | null | undefined, fallback = DASH): string {
  return fmtNum(v, 0, fallback)
}

export function fmtDistance(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return DASH
  return `${Math.round(v)}cm`
}

export function fmtPercent(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return DASH
  return `${Math.round(v)}%`
}

export function fmtVolt(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return DASH
  return `${v.toFixed(1)}V`
}

export function fmtRssi(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return DASH
  return `${Math.round(v)}dBm`
}

export function fmtTemp(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return DASH
  return `${Math.round(v)}°C`
}

export function fmtLatency(ms: number | null | undefined, offline: boolean): string {
  if (offline) return '离线'
  if (ms === null || ms === undefined || !Number.isFinite(ms) || ms <= 0) return DASH
  return `${Math.round(ms)}ms`
}

export function fmtTime(d: Date = new Date()): string {
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${hh}:${mm}`
}
