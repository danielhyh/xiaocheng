<script setup lang="ts">
import { computed } from 'vue'
import { useCarStore } from '../stores/carStore'

const props = defineProps<{
  isFullscreen: boolean
}>()

const emit = defineEmits<{
  toggleFullscreen: []
}>()

const store = useCarStore()

// 电池颜色
const batteryColor = computed(() => {
  switch (store.sensors.battery_level) {
    case 'critical': return '#e24b4a'
    case 'low':      return '#f5a623'
    default:         return '#2dd284'
  }
})

const batteryFill = computed(() =>
  Math.max(4, store.sensors.battery_percent)
)

const blinking = computed(() => store.sensors.battery_level === 'critical')

// CPU 温度颜色
const cpuColor = computed(() => {
  const t = store.sensors.cpu_temp
  if (t === null) return '#8a8d95'
  if (t >= 80) return '#e24b4a'
  if (t >= 65) return '#f5a623'
  return '#e8e6e1'
})

// WiFi 信号颜色
const wifiColor = computed(() => {
  const rssi = store.sensors.wifi_rssi
  if (rssi === null) return '#555860'
  if (rssi >= -50) return '#2dd284'
  if (rssi >= -70) return '#f5a623'
  return '#e24b4a'
})

// WiFi 信号格数 (1-3)
const wifiBars = computed(() => {
  const rssi = store.sensors.wifi_rssi
  if (rssi === null) return 0
  if (rssi >= -50) return 3
  if (rssi >= -70) return 2
  return 1
})

// 前方障碍物颜色
const obstacleColor = computed(() => {
  const d = store.sensors.front_distance
  if (d === null) return '#555860'
  if (d < 25) return '#e24b4a'
  if (d < 50) return '#f5a623'
  return '#8a8d95'
})
</script>

<template>
  <div class="topbar">
    <div class="topbar-left">
      <span class="brand">小橙</span>
      <span class="mode-chip">{{ store.mode }}</span>
      <span class="conn">
        <span class="dot" :class="store.connected ? 'on' : 'off'"></span>
        <span :style="{ color: store.connected ? '#2dd284' : '#e24b4a' }">
          {{ store.connected ? 'connected' : 'offline' }}
        </span>
      </span>
      <!-- WS 延迟 -->
      <span class="stat" v-if="store.wsLatency > 0">
        <span style="color: #555860">⏱</span>
        <b style="color: #8a8d95">{{ store.wsLatency }}ms</b>
      </span>
    </div>

    <div class="topbar-right">
      <!-- 前方障碍物距离 -->
      <span class="stat" v-if="store.sensors.front_distance !== null">
        <span :style="{ color: obstacleColor }">⟐</span>
        <b :style="{ color: obstacleColor }">
          {{ Math.round(store.sensors.front_distance!) }}cm
        </b>
      </span>

      <!-- WiFi 信号 -->
      <span class="wifi-wrap" v-if="store.sensors.wifi_rssi !== null">
        <svg class="wifi-icon" viewBox="0 0 16 12" :style="{ color: wifiColor }">
          <rect x="1" y="9" width="3" height="3" rx="0.5" fill="currentColor" :opacity="wifiBars >= 1 ? 1 : 0.2"/>
          <rect x="6" y="5" width="3" height="7" rx="0.5" fill="currentColor" :opacity="wifiBars >= 2 ? 1 : 0.2"/>
          <rect x="11" y="1" width="3" height="11" rx="0.5" fill="currentColor" :opacity="wifiBars >= 3 ? 1 : 0.2"/>
        </svg>
        <span class="wifi-val" :style="{ color: wifiColor }">{{ store.sensors.wifi_rssi }}dBm</span>
      </span>

      <!-- 电池 -->
      <span class="bat-wrap" :class="{ blink: blinking }">
        <span class="bat-icon" :style="{ borderColor: batteryColor }">
          <span
            class="bat-fill"
            :style="{ width: batteryFill + '%', background: batteryColor }"
          ></span>
          <span class="bat-tip" :style="{ background: batteryColor }"></span>
        </span>
        <span class="bat-text" :style="{ color: batteryColor }">
          {{ store.sensors.battery_percent }}%
        </span>
        <span class="bat-voltage">{{ store.sensors.battery_voltage.toFixed(1) }}V</span>
      </span>

      <!-- CPU 温度 + 占用率 -->
      <span class="stat">
        CPU
        <b :style="{ color: cpuColor }">
          {{ store.sensors.cpu_temp !== null ? Math.round(store.sensors.cpu_temp) + '°C' : '--' }}
        </b>
        <span class="cpu-usage" v-if="store.sensors.cpu_usage !== null">
          {{ Math.round(store.sensors.cpu_usage!) }}%
        </span>
      </span>

      <!-- 全屏按钮 -->
      <button class="fs-btn" :title="isFullscreen ? '退出全屏' : '全屏横屏'" @click="emit('toggleFullscreen')">
        <svg v-if="!isFullscreen" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 3h6v2H5v4H3V3z"/>
          <path d="M21 3h-6v2h4v4h2V3z"/>
          <path d="M3 21h6v-2H5v-4H3v6z"/>
          <path d="M21 21h-6v-2h4v-4h2v6z"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" aria-hidden="true">
          <path d="M9 3v6H3v-2h4V3h2z"/>
          <path d="M15 3v4h4v2h-6V3h2z"/>
          <path d="M9 21v-6H3v2h4v4h2z"/>
          <path d="M15 21v-4h4v-2h-6v6h2z"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.topbar {
  height: 36px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(13, 15, 20, 0.95);
  font-size: 12px;
  z-index: 10;
  flex-shrink: 0;
}

.topbar-left,
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand {
  font-weight: 700;
  font-size: 14px;
  color: #e8842c;
  letter-spacing: 1px;
}

.mode-chip {
  background: rgba(232, 132, 44, 0.15);
  color: #e8842c;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.conn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.dot.on  { background: #2dd284; }
.dot.off { background: #e24b4a; }

/* ---- WiFi ---- */
.wifi-wrap {
  display: flex;
  align-items: center;
  gap: 4px;
}
.wifi-icon {
  width: 16px;
  height: 12px;
}
.wifi-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
}

/* ---- 电池 ---- */
.bat-wrap {
  display: flex;
  align-items: center;
  gap: 5px;
}

.bat-icon {
  position: relative;
  display: flex;
  align-items: center;
  width: 28px;
  height: 13px;
  border: 1.5px solid;
  border-radius: 2px;
  overflow: visible;
  flex-shrink: 0;
}

.bat-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: 1px;
  transition: width 0.4s ease, background 0.4s ease;
}

.bat-tip {
  position: absolute;
  right: -5px;
  width: 3px;
  height: 6px;
  border-radius: 0 1px 1px 0;
}

.bat-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  transition: color 0.4s ease;
  min-width: 30px;
}

.bat-voltage {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #5a5d65;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}
.blink {
  animation: blink 0.8s ease-in-out infinite;
}

/* ---- CPU ---- */
.stat {
  color: #8a8d95;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 3px;
}
.stat b {
  font-weight: 500;
  transition: color 0.4s ease;
}
.cpu-usage {
  color: #555860;
  font-size: 10px;
}

/* ---- 全屏按钮 ---- */
.fs-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
  transition: background 0.15s;
}
.fs-btn:hover {
  background: rgba(255, 255, 255, 0.14);
}
.fs-btn:active {
  transform: scale(0.92);
}
.fs-btn svg {
  width: 16px;
  height: 16px;
  fill: #e8e6e1;
}
</style>
