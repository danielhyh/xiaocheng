<script setup lang="ts">
/**
 * MotionControl — 虚拟摇杆 + 速度环 + HUD
 *
 * 摇杆位移直接映射速度,无独立速度条。
 * 支持触屏拖拽 + WASD/方向键。
 * 输出归一化 vx/vy (-1~1)。
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useCarStore } from '../stores/carStore'

const emit = defineEmits<{
  move: [vx: number, vy: number]
}>()

const store = useCarStore()

// 摇杆状态
const thumbX = ref(0)
const thumbY = ref(0)
const active = ref(false)
const inputLocked = ref(false)

const RADIUS = 50  // 最大偏移像素
const SEND_INTERVAL_MS = 100
let repeatTimer: number | null = null

// 归一化输出
const vx = computed(() => Math.round(thumbX.value / RADIUS * 100) / 100)
const vy = computed(() => Math.round(-thumbY.value / RADIUS * 100) / 100)
const speed = computed(() => {
  const s = Math.sqrt(vx.value ** 2 + vy.value ** 2)
  return Math.min(Math.round(s * 100), 100)
})

// 速度环 SVG
const arcOffset = computed(() => {
  const circ = 188.5
  return circ - circ * speed.value / 100
})

// ---- 触屏/鼠标 ----
let baseRect: DOMRect | null = null
const baseEl = ref<HTMLElement>()

function getCenter() {
  baseRect = baseEl.value?.getBoundingClientRect() ?? null
  if (!baseRect) return { x: 0, y: 0 }
  return { x: baseRect.left + baseRect.width / 2, y: baseRect.top + baseRect.height / 2 }
}

function applyMove(dx: number, dy: number) {
  if (inputLocked.value) return
  const dist = Math.sqrt(dx * dx + dy * dy)
  if (dist > RADIUS) {
    dx = dx / dist * RADIUS
    dy = dy / dist * RADIUS
  }
  thumbX.value = dx
  thumbY.value = dy
  emit('move', vx.value, vy.value)
}

function startRepeatSend() {
  if (inputLocked.value) return
  if (repeatTimer !== null) return
  repeatTimer = window.setInterval(() => {
    emit('move', vx.value, vy.value)
  }, SEND_INTERVAL_MS)
}

function stopRepeatSend() {
  if (repeatTimer === null) return
  clearInterval(repeatTimer)
  repeatTimer = null
}

function onPointerDown(e: PointerEvent) {
  e.preventDefault()
  if (inputLocked.value) return
  active.value = true
  const c = getCenter()
  applyMove(e.clientX - c.x, e.clientY - c.y)
  startRepeatSend()
  ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (!active.value || inputLocked.value) return
  const c = getCenter()
  applyMove(e.clientX - c.x, e.clientY - c.y)
}

function onPointerUp() {
  inputLocked.value = false
  active.value = false
  stopRepeatSend()
  thumbX.value = 0
  thumbY.value = 0
  emit('move', 0, 0)
}

// ---- 键盘 (WASD) ----
const keys = new Set<string>()

function applyKeys() {
  if (inputLocked.value) return
  let dx = 0, dy = 0
  if (keys.has('w') || keys.has('arrowup'))    dy = -RADIUS
  if (keys.has('s') || keys.has('arrowdown'))  dy =  RADIUS
  if (keys.has('a') || keys.has('arrowleft'))  dx = -RADIUS
  if (keys.has('d') || keys.has('arrowright')) dx =  RADIUS
  applyMove(dx, dy)
}

function onKeyDown(e: KeyboardEvent) {
  const k = e.key.toLowerCase()
  if ('wasd'.includes(k) || k.startsWith('arrow')) {
    e.preventDefault()
    if (inputLocked.value) return
    keys.add(k)
    active.value = true
    applyKeys()
    startRepeatSend()
  }
}

function onKeyUp(e: KeyboardEvent) {
  const k = e.key.toLowerCase()
  keys.delete(k)
  if (inputLocked.value && keys.size === 0) {
    inputLocked.value = false
  }
  if (keys.size === 0) {
    active.value = false
    stopRepeatSend()
    thumbX.value = 0
    thumbY.value = 0
    emit('move', 0, 0)
  } else {
    applyKeys()
  }
}

function resetControls() {
  const shouldLockInput = active.value || keys.size > 0
  keys.clear()
  inputLocked.value = shouldLockInput
  active.value = false
  stopRepeatSend()
  thumbX.value = 0
  thumbY.value = 0
  emit('move', 0, 0)
}

defineExpose({
  resetControls,
})

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  stopRepeatSend()
})
</script>

<template>
  <div class="motion-zone">
    <!-- 摇杆 -->
    <div class="joy-wrap">
      <div
        ref="baseEl"
        class="joy-base"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
      >
        <div class="joy-ring"></div>
        <span class="hint u">W</span>
        <span class="hint d">S</span>
        <span class="hint l">A</span>
        <span class="hint r">D</span>
        <div
          class="joy-thumb"
          :class="{ active }"
          :style="{ transform: `translate(calc(-50% + ${thumbX}px), calc(-50% + ${thumbY}px))` }"
        ></div>
      </div>
      <span class="joy-label">move</span>
    </div>

    <!-- 速度环 -->
    <svg class="speed-ring" viewBox="0 0 72 72">
      <circle cx="36" cy="36" r="30" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="3"/>
      <circle cx="36" cy="36" r="30" fill="none" stroke="#e8842c" stroke-width="3"
        :stroke-dasharray="188.5" :stroke-dashoffset="arcOffset"
        stroke-linecap="round" transform="rotate(-90 36 36)"/>
      <text x="36" y="34" text-anchor="middle" font-size="16" font-weight="700" fill="#e8842c"
        font-family="JetBrains Mono, monospace">{{ speed }}</text>
      <text x="36" y="46" text-anchor="middle" font-size="11" fill="#555860"
        font-family="JetBrains Mono, monospace">%</text>
    </svg>

    <!-- HUD 读数 -->
    <div class="hud">
      <div class="hud-row">
        <span class="hud-lbl">DIR</span>
        <span class="hud-val hi">{{ store.motion.direction.toUpperCase() }}</span>
      </div>
      <div class="hud-row">
        <span class="hud-lbl">VX</span>
        <span class="hud-val">{{ store.motion.vx.toFixed(2) }}</span>
      </div>
      <div class="hud-row">
        <span class="hud-lbl">VY</span>
        <span class="hud-val">{{ store.motion.vy.toFixed(2) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.motion-zone {
  position: absolute; bottom: 20px; left: 20px;
  display: flex; align-items: flex-end; gap: 16px;
  z-index: 20;
}

/* 摇杆 */
.joy-wrap { position: relative; }
.joy-base {
  width: 150px; height: 150px; border-radius: 50%;
  background: rgba(255,255,255,0.06); border: 1.5px solid rgba(255,255,255,0.15);
  position: relative; touch-action: none;
}
.joy-ring {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 108px; height: 108px; border-radius: 50%;
  border: 1px dashed rgba(255,255,255,0.12);
}
.joy-thumb {
  position: absolute; top: 50%; left: 50%;
  width: 52px; height: 52px; border-radius: 50%;
  background: rgba(232,132,44,0.25); border: 2px solid #e8842c;
  transform: translate(-50%,-50%); cursor: grab;
  transition: box-shadow 0.15s;
}
.joy-thumb.active {
  cursor: grabbing;
  box-shadow: 0 0 24px rgba(232,132,44,0.25);
}
.joy-label {
  display: block; text-align: center; margin-top: 4px;
  font-size: 11px; color: #555860; letter-spacing: 1px;
}
.hint {
  position: absolute; font-size: 11px; color: #8a8d95; font-weight: 600;
  pointer-events: none;
}
.hint.u { top: 4px; left: 50%; transform: translateX(-50%); }
.hint.d { bottom: 4px; left: 50%; transform: translateX(-50%); }
.hint.l { left: 6px; top: 50%; transform: translateY(-50%); }
.hint.r { right: 6px; top: 50%; transform: translateY(-50%); }

/* 速度环 */
.speed-ring { width: 72px; height: 72px; margin-bottom: 30px; }

/* HUD */
.hud {
  display: flex; flex-direction: column; gap: 4px;
  font-family: 'JetBrains Mono', monospace; font-size: 12px;
  margin-bottom: 30px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 6px;
  padding: 6px 8px;
}
.hud-row { display: flex; align-items: center; gap: 6px; }
.hud-lbl { color: #555860; width: 32px; text-align: right; }
.hud-val { color: #8a8d95; min-width: 44px; }
.hud-val.hi { color: #e8842c; }
</style>
