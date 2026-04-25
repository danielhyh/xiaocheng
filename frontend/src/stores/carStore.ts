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

  // 运动遥测 (tel.motion)
  const motion = reactive({
    vx: 0,
    vy: 0,
    speed: 0,
    direction: 'idle',
    left_speed: 0,
    right_speed: 0,
  })

  // 传感器遥测 (tel.sensors)
  const sensors = reactive({
    battery_voltage: 0,
    cpu_temp: 0,
    cpu_usage: 0,
    wifi_rssi: 0,
    ws_latency_ms: 0,
  })

  function updateMotion(payload: any) {
    Object.assign(motion, payload)
  }

  function updateSensors(payload: any) {
    Object.assign(sensors, payload)
  }

  return {
    connected,
    mode,
    motion,
    sensors,
    updateMotion,
    updateSensors,
  }
})
