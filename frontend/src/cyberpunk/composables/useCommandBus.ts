/**
 * useCommandBus — 所有 cmd.* 的统一出口
 *
 * 目标: 把旧版 App.vue 的发送函数集中封装, 新组件只依赖这个 bus,
 * 避免每个组件自行持有 ws 引用。
 *
 * 合约:
 *   - 只发送 cmd.* 类型 (R17.3)
 *   - payload 字段与后端 dispatcher 现有解析保持一致
 */

import type { Ref } from 'vue'
import type { useWebSocket } from '../../composables/useWebSocket'

type Ws = ReturnType<typeof useWebSocket>

export interface MotionVec {
  vx: number
  vy: number
}

export interface GimbalVec {
  pan: number
  tilt: number
}

export function useCommandBus(ws: Ws) {
  // ---- 运动 ----
  function sendMotion(vx: number, vy: number) {
    ws.send('cmd.motion', { vx, vy })
  }

  function sendBrake() {
    ws.send('cmd.brake', {})
  }

  // ---- 云台 ----
  // 兼容旧后端: cmd.gimbal 用 action=move, data={dx, dy}
  function sendGimbal(pan: number, tilt: number) {
    ws.send('cmd.gimbal', {
      action: 'move',
      data: { dx: pan, dy: tilt },
    })
  }

  function sendGimbalCenter() {
    ws.send('cmd.gimbal', { action: 'center' }, 'gimbal-center')
  }

  // ---- 鸣笛 ----
  function sendHornShort() {
    ws.send('cmd.audio', { action: 'play', data: { clip: 'horn' } })
  }

  function sendHornStart() {
    ws.send('cmd.audio', { action: 'horn_start' })
  }

  function sendHornStop() {
    ws.send('cmd.audio', { action: 'horn_stop' })
  }

  // ---- 音响 ----
  function sendVolume(level: number) {
    ws.send('cmd.audio', { action: 'volume', data: { level } })
  }

  function sendTts(text: string, voice?: string) {
    ws.send('cmd.audio', {
      action: 'tts',
      data: { text, voice: voice ?? '' },
    })
  }

  function sendAudioStop() {
    ws.send('cmd.audio', { action: 'stop' })
  }

  // ---- 灯光 ----
  function sendHeadlight(data: { on?: boolean; brightness?: number }) {
    ws.send('cmd.light', { action: 'headlight', data }, 'light-hl')
  }

  function sendStripMode(mode: string) {
    ws.send('cmd.light', { action: 'strip_mode', data: { mode } }, 'light-sm')
  }

  // ---- 模式 ----
  function sendMode(mode: 'manual' | 'avoid' | 'track' | 'nav' | 'voice') {
    ws.send('cmd.mode', { mode }, 'mode-switch')
  }

  // ---- 心跳 ----
  function sendPing() {
    ws.send('cmd.ping', {})
  }

  return {
    sendMotion,
    sendBrake,
    sendGimbal,
    sendGimbalCenter,
    sendHornShort,
    sendHornStart,
    sendHornStop,
    sendVolume,
    sendTts,
    sendAudioStop,
    sendHeadlight,
    sendStripMode,
    sendMode,
    sendPing,
  }
}

export type CommandBus = ReturnType<typeof useCommandBus>
