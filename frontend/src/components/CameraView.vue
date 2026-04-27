<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useCarStore } from '../stores/carStore'

const store = useCarStore()

// MJPEG 流地址: 与后端同源
const streamUrl = computed(() => {
  const base = `${location.protocol}//${location.hostname}:${location.port || 8000}`
  return `${base}/stream/camera`
})

const isLoading = ref(true)
const hasError = ref(false)
let retryTimer: number | null = null

function onLoad() {
  isLoading.value = false
  hasError.value = false
}

function onError() {
  isLoading.value = false
  hasError.value = true
  scheduleRetry()
}

function scheduleRetry() {
  if (retryTimer) return
  retryTimer = window.setTimeout(() => {
    retryTimer = null
    hasError.value = false
    isLoading.value = true
    imgKey.value++
  }, 3000)
}

const imgKey = ref(0)

// ---- 帧率 + 延迟 HUD ----
const streamFps = ref(0)
const streamRes = ref('')
const wsLatency = ref(0)
let statusTimer: number | null = null

async function fetchStreamStatus() {
  try {
    const base = `${location.protocol}//${location.hostname}:${location.port || 8000}`
    const res = await fetch(`${base}/stream/status`)
    if (res.ok) {
      const data = await res.json()
      streamFps.value = data.fps || 0
      if (data.resolution && data.resolution.length === 2) {
        streamRes.value = `${data.resolution[0]}×${data.resolution[1]}`
      }
    }
  } catch { /* ignore */ }
}

onMounted(() => {
  // 每 2 秒拉一次流状态
  statusTimer = window.setInterval(fetchStreamStatus, 2000)
  fetchStreamStatus()
})

onUnmounted(() => {
  if (retryTimer) {
    clearTimeout(retryTimer)
    retryTimer = null
  }
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
})
</script>

<template>
  <div class="camera-view">
    <!-- MJPEG 流 -->
    <img
      v-if="!hasError"
      :key="imgKey"
      :src="streamUrl"
      class="stream"
      alt="FPV Camera"
      @load="onLoad"
      @error="onError"
    />

    <!-- 加载中 -->
    <div v-if="isLoading && !hasError" class="placeholder">
      <div class="spinner"></div>
      <span class="label">连接摄像头...</span>
    </div>

    <!-- 离线 -->
    <div v-if="hasError" class="placeholder">
      <div class="cam-icon">
        <div class="cam-inner"></div>
      </div>
      <span class="label">Camera offline</span>
      <span class="phase">重连中...</span>
    </div>

    <!-- 帧率 / 分辨率 / 延迟 HUD (左上角) -->
    <div class="stream-hud" v-if="!hasError && !isLoading">
      <span class="hud-item" v-if="streamRes">
        <span class="hud-icon">⬚</span>
        <span class="hud-num">{{ streamRes }}</span>
      </span>
      <span class="hud-item">
        <span class="hud-icon">◉</span>
        <span class="hud-num">{{ streamFps.toFixed(0) }}</span>
        <span class="hud-unit">FPS</span>
      </span>
      <span class="hud-item" v-if="store.wsLatency > 0">
        <span class="hud-icon">⏱</span>
        <span class="hud-num">{{ store.wsLatency }}</span>
        <span class="hud-unit">ms</span>
      </span>
    </div>

    <!-- HUD 叠加层: 十字准星 + 角落框 -->
    <div class="crosshair"></div>
    <div class="bracket tl"></div>
    <div class="bracket tr"></div>
    <div class="bracket bl"></div>
    <div class="bracket br"></div>
  </div>
</template>

<style scoped>
.camera-view {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: #0a0c10;
}

.stream {
  width: 100%; height: 100%;
  object-fit: cover;
}

.placeholder {
  position: absolute;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  color: #555860; font-size: 13px; font-weight: 500;
}
.cam-icon {
  width: 40px; height: 40px; border: 2px solid #555860;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.cam-inner { width: 16px; height: 16px; border: 2px solid #555860; border-radius: 50%; }
.phase { font-size: 11px; }

.spinner {
  width: 28px; height: 28px;
  border: 2px solid #333;
  border-top-color: #e8842c;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ---- 帧率/延迟 HUD ---- */
.stream-hud {
  position: absolute;
  top: 8px; left: 8px;
  display: flex; gap: 10px;
  background: rgba(0, 0, 0, 0.55);
  border-radius: 6px;
  padding: 3px 8px;
  pointer-events: none;
  z-index: 5;
}
.hud-item {
  display: flex; align-items: center; gap: 3px;
  font-family: 'JetBrains Mono', monospace;
}
.hud-icon {
  font-size: 8px;
  color: #2dd284;
}
.hud-num {
  font-size: 12px;
  font-weight: 600;
  color: #e8e6e1;
}
.hud-unit {
  font-size: 9px;
  color: #8a8d95;
}

/* ---- 准星 + 角落框 ---- */
.crosshair {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 60px; height: 60px; opacity: 0.15; pointer-events: none;
}
.crosshair::before, .crosshair::after {
  content: ''; position: absolute; background: #e8e6e1;
}
.crosshair::before { width: 1px; height: 100%; left: 50%; }
.crosshair::after  { height: 1px; width: 100%; top: 50%; }

.bracket {
  position: absolute; width: 18px; height: 18px;
  border-color: #e8842c; border-style: solid; border-width: 0;
  opacity: 0.3; pointer-events: none;
}
.bracket.tl { top: 20%; left: 15%; border-top-width: 2px; border-left-width: 2px; }
.bracket.tr { top: 20%; right: 15%; border-top-width: 2px; border-right-width: 2px; }
.bracket.bl { bottom: 20%; left: 15%; border-bottom-width: 2px; border-left-width: 2px; }
.bracket.br { bottom: 20%; right: 15%; border-bottom-width: 2px; border-right-width: 2px; }
</style>
