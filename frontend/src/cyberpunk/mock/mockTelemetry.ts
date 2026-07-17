/**
 * mockTelemetry — 前端内置 Mock 遥测数据源
 *
 * 完全不需要后端。模拟 WS 连接 + 周期性推送 tel.motion / tel.sensors,
 * 让 HUD 上的 FPS、延迟、电量、CPU 温度等全部有数据显示。
 *
 * 用法:
 *   在 CyberpunkPanel 中检测 mock 模式时, 调用 startMockTelemetry(store)
 *   即可让 store 持续收到模拟数据。
 */

import type { useCarStore } from '../../stores/carStore'

type Store = ReturnType<typeof useCarStore>

export interface MockConfig {
  /** 模拟连接状态 */
  connected: boolean
  /** 模拟电池电压 */
  batteryVoltage: number
  /** 模拟电池百分比 */
  batteryPercent: number
  /** 模拟电池档位 */
  batteryLevel: 'ok' | 'low' | 'critical' | 'unknown'
  /** 模拟 WiFi RSSI */
  wifiRssi: number
  /** 模拟 CPU 温度 */
  cpuTemp: number
  /** 模拟 WS 延迟 */
  wsLatency: number
  /** 模拟前方距离 */
  frontDistance: number
  /** 模拟后方距离 */
  rearDistance: number
  /** 模拟 FPS */
  fps: number
}

const DEFAULT_CONFIG: MockConfig = {
  connected: true,
  batteryVoltage: 7.8,
  batteryPercent: 82,
  batteryLevel: 'ok',
  wifiRssi: -62,
  cpuTemp: 52,
  wsLatency: 23,
  frontDistance: 120,
  rearDistance: 85,
  fps: 30,
}

let _timer: number | null = null
let _config: MockConfig = { ...DEFAULT_CONFIG }

/**
 * 获取当前 mock 配置 (可在 DevTools console 中修改)
 */
export function getMockConfig(): MockConfig {
  return _config
}

/**
 * 更新 mock 配置
 */
export function setMockConfig(partial: Partial<MockConfig>) {
  Object.assign(_config, partial)
}

/**
 * 启动 mock 遥测推送
 */
export function startMockTelemetry(store: Store) {
  if (_timer !== null) return

  // 立即设置连接状态
  store.connected = _config.connected
  store.wsLatency = _config.wsLatency

  // 模拟 tel.sensors 每 1s
  _timer = window.setInterval(() => {
    store.connected = _config.connected
    store.wsLatency = _config.wsLatency + Math.round((Math.random() - 0.5) * 6)

    store.updateSensors({
      battery_voltage: _config.batteryVoltage + (Math.random() - 0.5) * 0.05,
      battery_percent: _config.batteryPercent,
      battery_level: _config.batteryLevel,
      cpu_temp: _config.cpuTemp + (Math.random() - 0.5) * 2,
      wifi_rssi: _config.wifiRssi + Math.round((Math.random() - 0.5) * 4),
      cpu_usage: 15 + Math.random() * 10,
      gimbal_pan: 90,
      gimbal_tilt: 90,
      front_distance: _config.frontDistance + (Math.random() - 0.5) * 5,
      rear_distance: _config.rearDistance + (Math.random() - 0.5) * 5,
      front_blocked: false,
      rear_blocked: false,
    })
  }, 1000)

  // 模拟 tel.motion 每 100ms
  window.setInterval(() => {
    store.updateMotion({
      vx: store.motion.vx,
      vy: store.motion.vy,
      speed: Math.sqrt(store.motion.vx ** 2 + store.motion.vy ** 2) * 1.8,
      direction: getDirection(store.motion.vx, store.motion.vy),
      left_speed: 0,
      right_speed: 0,
      nitro_active: false,
      nitro_boost: 1.0,
    })
  }, 100)

  // 暴露到 window 方便 DevTools 调试
  ;(window as any).__mockCar = {
    get config() { return _config },
    set(partial: Partial<MockConfig>) {
      setMockConfig(partial)
      console.log('[Mock] 配置已更新:', _config)
    },
    disconnect() {
      setMockConfig({ connected: false })
      console.log('[Mock] 已断开')
    },
    connect() {
      setMockConfig({ connected: true })
      console.log('[Mock] 已连接')
    },
    lowBattery() {
      setMockConfig({ batteryLevel: 'low', batteryPercent: 25, batteryVoltage: 6.9 })
      console.log('[Mock] 低电量')
    },
    criticalBattery() {
      setMockConfig({ batteryLevel: 'critical', batteryPercent: 8, batteryVoltage: 6.1 })
      console.log('[Mock] 危险电量')
    },
    okBattery() {
      setMockConfig({ batteryLevel: 'ok', batteryPercent: 82, batteryVoltage: 7.8 })
      console.log('[Mock] 正常电量')
    },
  }

  console.log(
    '%c[Mock 模式已启动]%c\n' +
    '在 DevTools Console 中使用:\n' +
    '  __mockCar.disconnect()     — 模拟断开\n' +
    '  __mockCar.connect()        — 模拟连接\n' +
    '  __mockCar.lowBattery()     — 模拟低电量\n' +
    '  __mockCar.criticalBattery()— 模拟危险电量\n' +
    '  __mockCar.set({ cpuTemp: 80, wsLatency: 100 }) — 自定义\n',
    'color: #34e0ff; font-weight: bold; font-size: 14px',
    'color: #ccc',
  )
}

/**
 * 停止 mock 遥测
 */
export function stopMockTelemetry() {
  if (_timer !== null) {
    window.clearInterval(_timer)
    _timer = null
  }
}

function getDirection(vx: number, vy: number): string {
  if (Math.abs(vx) < 0.05 && Math.abs(vy) < 0.05) return 'idle'
  if (vy > 0.3) return vx > 0.3 ? 'forward-right' : vx < -0.3 ? 'forward-left' : 'forward'
  if (vy < -0.3) return vx > 0.3 ? 'reverse-right' : vx < -0.3 ? 'reverse-left' : 'reverse'
  return vx > 0 ? 'right' : 'left'
}
