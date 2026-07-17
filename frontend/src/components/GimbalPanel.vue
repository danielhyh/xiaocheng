<script setup lang="ts">
/**
 * GimbalPanel — 云台控制面板
 *
 * 功能:
 *   - 小摇杆控制 pan/tilt
 *   - 回中按钮
 *   - 当前角度显示
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useCarStore } from '../stores/carStore'

const store = useCarStore()

const emit = defineEmits<{
  close: []
  gimbalMove: [data: { dx: number; dy: number }]
  gimbalCenter: []
}>()

// 迷你摇杆
const thumbX = ref(0)
const thumbY = ref(0)
const active = ref(false)
const baseEl = ref<HTMLElement>()
const RADIUS = 35
let sendTimer: number | null = null

function getCenter() {
  const rect = baseEl.value?.getBoundingClientRect()
  if (!rect) return { x: 0, y: 0 }
  return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
}

function applyMove(dx: number, dy: number) {
  const dist = Math.sqrt(dx * dx + dy * dy)
  if (dist > RADIUS) {
    dx = dx / dist * RADIUS
    dy = dy / dist * RADIUS
  }
  thumbX.value = dx
  thumbY.value = dy
}

function startSend() {
  if (sendTimer !== null) return
  sendTimer = window.setInterval(() => {
    const dx = thumbX.value / RADIUS
    const dy = -thumbY.value / RADIUS  // 上为正
    if (Math.abs(dx) > 0.05 || Math.abs(dy) > 0.05) {
      emit('gimbalMove', { dx, dy })
    }
  }, 100)
}

function stopSend() {
  if (sendTimer !== null) {
    clearInterval(sendTimer)
    sendTimer = null
  }
}

function onPointerDown(e: PointerEvent) {
  e.preventDefault()
  active.value = true
  const c = getCenter()
  applyMove(e.clientX - c.x, e.clientY - c.y)
  startSend()
  ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (!active.value) return
  const c = getCenter()
  applyMove(e.clientX - c.x, e.clientY - c.y)
}

function onPointerUp() {
  active.value = false
  stopSend()
  thumbX.value = 0
  thumbY.value = 0
}

function onCenter() {
  emit('gimbalCenter')
}

onUnmounted(() => {
  stopSend()
})
</script>

<template>
  <div class="gimbal-panel" @click.stop>
    <button class="close-btn" @click="emit('close')" title="关闭">✕</button>
    <div class="panel-title">云台控制</div>

    <!-- 角度显示 -->
    <div class="angle-display">
      <div class="angle-item">
        <span class="angle-label">PAN</span>
        <span class="angle-value">{{ store.sensors.gimbal_pan?.toFixed(0) ?? 90 }}°</span>
      </div>
      <div class="angle-item">
        <span class="angle-label">TILT</span>
        <span class="angle-value">{{ store.sensors.gimbal_tilt?.toFixed(0) ?? 90 }}°</span>
      </div>
    </div>

    <!-- 迷你摇杆 -->
    <div class="joy-area">
      <div
        ref="baseEl"
        class="mini-joy-base"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
      >
        <div class="mini-joy-ring"></div>
        <div
          class="mini-joy-thumb"
          :class="{ active }"
          :style="{ transform: `translate(calc(-50% + ${thumbX}px), calc(-50% + ${thumbY}px))` }"
        ></div>
      </div>
    </div>

    <!-- 回中按钮 -->
    <button class="center-btn" @click="onCenter">回中</button>
  </div>
</template>

<style scoped>
.gimbal-panel {
  position: absolute;
  right: 72px;
  top: 50%;
  transform: translateY(-50%);
  width: 180px;
  background: rgba(20, 22, 30, 0.95);
  border: 1px solid rgba(45, 210, 132, 0.25);
  border-radius: 14px;
  padding: 14px;
  z-index: 30;
  backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.close-btn {
  position: absolute;
  top: 8px; right: 10px;
  background: none; border: none;
  color: #666; font-size: 14px;
  cursor: pointer; padding: 2px 6px;
}
.close-btn:hover { color: #aaa; }

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #e8e6e1;
}

.angle-display {
  display: flex; gap: 16px;
  font-family: 'JetBrains Mono', monospace;
}
.angle-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.angle-label { font-size: 10px; color: #555860; }
.angle-value { font-size: 14px; color: #2dd284; font-weight: 600; }

.joy-area {
  display: flex; align-items: center; justify-content: center;
}

.mini-joy-base {
  width: 90px; height: 90px; border-radius: 50%;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(45, 210, 132, 0.2);
  position: relative; touch-action: none;
}
.mini-joy-ring {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  width: 65px; height: 65px; border-radius: 50%;
  border: 1px dashed rgba(45, 210, 132, 0.15);
}
.mini-joy-thumb {
  position: absolute; top: 50%; left: 50%;
  width: 30px; height: 30px; border-radius: 50%;
  background: rgba(45, 210, 132, 0.2);
  border: 2px solid #2dd284;
  transform: translate(-50%,-50%);
  cursor: grab;
  transition: box-shadow 0.15s;
}
.mini-joy-thumb.active {
  cursor: grabbing;
  box-shadow: 0 0 16px rgba(45, 210, 132, 0.3);
}

.center-btn {
  width: 100%;
  height: 28px;
  border-radius: 6px;
  background: rgba(45, 210, 132, 0.15);
  border: 1px solid rgba(45, 210, 132, 0.3);
  color: #2dd284;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.center-btn:hover { background: rgba(45, 210, 132, 0.25); }
</style>
