/**
 * carStore — 全局车辆状态
 *
 * 缓存遥测数据, UI 组件从这里读取。
 * useWebSocket 收到 tel.* 消息后写入这里。
 */

import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export const useCarStore = defineStore('car', () => {
  // 连接状态
  const connected = ref(false)
  const mode = ref('manual')
  const wsLatency = ref(0)

  // 运动遥测 (tel.motion)
  const motion = reactive({
    vx: 0,
    vy: 0,
    speed: 0,
    direction: 'idle',
    left_speed: 0,
    right_speed: 0,
    nitro_active: false,
    nitro_boost: 1.0,
  })

  // 传感器遥测 (tel.sensors)
  const sensors = reactive({
    battery_voltage: null as number | null,
    battery_percent: null as number | null,
    battery_level: 'unknown' as 'ok' | 'low' | 'critical' | 'unknown',
    cpu_temp: null as number | null,
    // Phase 7 增强
    wifi_rssi: null as number | null,
    cpu_usage: null as number | null,
    // Phase 4 云台
    gimbal_pan: null as number | null,
    gimbal_tilt: null as number | null,
    // Phase 6 避障
    front_distance: null as number | null,
    rear_distance: null as number | null,
    front_blocked: false,
    rear_blocked: false,
  })

  // 灯光状态
  const lighting = reactive({
    headlight_on: false,
    headlight_brightness: 80,
    strip_mode: 'off' as string,
  })

  // 氮气状态
  const nitro = reactive({
    active: false,
    cooling: false,
    cooldown_remaining: 0,
  })

  function updateMotion(payload: any) {
    Object.assign(motion, payload)
  }

  function updateSensors(payload: any) {
    Object.assign(sensors, payload)
  }

  function updateLighting(payload: any) {
    Object.assign(lighting, payload)
  }

  function updateNitro(payload: any) {
    Object.assign(nitro, payload)
  }

  return {
    connected,
    mode,
    wsLatency,
    motion,
    sensors,
    lighting,
    nitro,
    updateMotion,
    updateSensors,
    updateLighting,
    updateNitro,
  }
})
