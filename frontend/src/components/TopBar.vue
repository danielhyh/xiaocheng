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

// 电池颜色：跟随 level
const batteryColor = computed(() => {
  switch (store.sensors.battery_level) {
    case 'critical': return '#e24b4a'
    case 'low':      return '#f5a623'
    default:         return '#2dd284'
  }
})

// 电池图标内部填充宽度（最小 4% 保留轮廓可见）
const batteryFill = computed(() =>
  Math.max(4, store.sensors.battery_percent)
)

// 电量极低时闪烁
const blinking = computed(() => store.sensors.battery_level === 'critical')

// CPU 温度颜色
const cpuColor = computed(() => {
  const t = store.sensors.cpu_temp
  if (t === null) return '#8a8d95'
  if (t >= 80) return '#e24b4a'
  if (t >= 65) return '#f5a623'
  return '#e8e6e1'
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
    </div>

    <div class="topbar-right">
      <!-- 电池组件 -->
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

      <!-- CPU 温度 -->
      <span class="stat">
        CPU
        <b :style="{ color: cpuColor }">
          {{ store.sensors.cpu_temp !== null ? Math.round(store.sensors.cpu_temp) + '°C' : '--' }}
        </b>
      </span>

      <!-- 全屏按钮 -->
      <button class="fs-btn" :title="isFullscreen ? '退出全屏' : '全屏横屏'" @click="emit('toggleFullscreen')">
        <!-- 进入全屏图标 -->
        <svg v-if="!isFullscreen" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 3h6v2H5v4H3V3z"/>
          <path d="M21 3h-6v2h4v4h2V3z"/>
          <path d="M3 21h6v-2H5v-4H3v6z"/>
          <path d="M21 21h-6v-2h4v-4h2v6z"/>
        </svg>
        <!-- 退出全屏图标 -->
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
}
.stat b {
  font-weight: 500;
  transition: color 0.4s ease;
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
