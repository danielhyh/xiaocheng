<!--
  MoveJoystick — 左下虚拟移动摇杆 (R6)

  外圆直径 120px, clampToUnitDisk 归一化向量 (vx, vy)
  KeepaliveService 100ms 保活 (首帧即时发)
  释放 / pointercancel / pointerleave → 立即回中并发送 (0,0)
-->

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { normalizeOffset } from '../utils/joystick'
import { useKeepaliveSender } from '../composables/useKeepaliveSender'
import type { CommandBus } from '../composables/useCommandBus'
import type { MotionVec } from '../composables/useCommandBus'
import wheelCenterUrl from '../../assets/cyberpunk/joystick-thumb.png'
import rouletteBottomUrl from '../../assets/cyberpunk/joystick-base.png'

const props = defineProps<{ bus: CommandBus }>()

const DIAMETER = 140
const RADIUS = DIAMETER / 2
const THUMB_NUB = 48
const THUMB_NUB_R = THUMB_NUB / 2
// 拇指边缘刚好卡在轮盘边界：行程 = 轮盘半径 - 拇指半径
const TRAVEL = RADIUS - THUMB_NUB_R
const DEADZONE = 0.04

const baseEl = ref<HTMLDivElement>()
const thumbVec = ref({ x: 0, y: 0 })  // 归一化, 正向屏幕坐标 (y 向下为正)
const active = ref(false)
const keysHeld = ref(new Set<string>())

const sender = useKeepaliveSender<MotionVec>({
  emit: (p) => props.bus.sendMotion(p.vx, p.vy),
  periodMs: 100,
})

// 屏幕坐标 (y 向下) → 运动向量 (y 向上为前进)
const currentPayload = computed<MotionVec>(() => {
  const raw = {
    vx: Math.abs(thumbVec.value.x) < DEADZONE ? 0 : thumbVec.value.x,
    vy: Math.abs(-thumbVec.value.y) < DEADZONE ? 0 : -thumbVec.value.y,
  }
  return {
    vx: Number(raw.vx.toFixed(3)),
    vy: Number(raw.vy.toFixed(3)),
  }
})

function getCenter() {
  const r = baseEl.value?.getBoundingClientRect()
  if (!r) return { x: 0, y: 0 }
  return { x: r.left + r.width / 2, y: r.top + r.height / 2 }
}

function applyFromPointer(clientX: number, clientY: number) {
  const c = getCenter()
  thumbVec.value = normalizeOffset(clientX - c.x, clientY - c.y, RADIUS)
  sender.setPayload(currentPayload.value)
}

function onPointerDown(e: PointerEvent) {
  e.preventDefault()
  active.value = true
  ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
  applyFromPointer(e.clientX, e.clientY)
  sender.start(currentPayload.value)
}

function onPointerMove(e: PointerEvent) {
  if (!active.value) return
  applyFromPointer(e.clientX, e.clientY)
}

function release() {
  if (!active.value && !sender.isRunning()) return
  active.value = false
  thumbVec.value = { x: 0, y: 0 }
  // R6.4 / R6.6: 立即回中并发送 (0, 0)
  sender.stop({ vx: 0, vy: 0 })
}

function onPointerUp() { release() }
function onPointerCancel() { release() }
function onPointerLeave() { if (active.value) release() }

// ---- 键盘 (WASD / Arrow keys) 作为辅助 ----
function updateFromKeys() {
  let dx = 0, dy = 0
  if (keysHeld.value.has('w') || keysHeld.value.has('arrowup'))    dy -= RADIUS
  if (keysHeld.value.has('s') || keysHeld.value.has('arrowdown'))  dy += RADIUS
  if (keysHeld.value.has('a') || keysHeld.value.has('arrowleft'))  dx -= RADIUS
  if (keysHeld.value.has('d') || keysHeld.value.has('arrowright')) dx += RADIUS
  thumbVec.value = normalizeOffset(dx, dy, RADIUS)
  sender.setPayload(currentPayload.value)
}

function onKeyDown(e: KeyboardEvent) {
  const k = e.key.toLowerCase()
  if (!'wasd'.includes(k) && !k.startsWith('arrow')) return
  e.preventDefault()
  const wasEmpty = keysHeld.value.size === 0
  keysHeld.value.add(k)
  updateFromKeys()
  if (wasEmpty) {
    sender.start(currentPayload.value)
    active.value = true
  }
}

function onKeyUp(e: KeyboardEvent) {
  const k = e.key.toLowerCase()
  if (!keysHeld.value.has(k)) return
  keysHeld.value.delete(k)
  if (keysHeld.value.size === 0) {
    release()
  } else {
    updateFromKeys()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
})

defineExpose({
  /** 紧急停止: BRAKE 时复位摇杆并发送 (0,0) */
  reset: release,
})
</script>

<template>
  <div class="move-joystick absolute bottom-6 left-6 z-20 flex flex-col items-center
              select-none">
    <div class="relative rounded-full p-[3px]">
      <div
        ref="baseEl"
        class="relative rounded-full touch-none overflow-hidden"
        role="application"
        aria-label="车辆移动摇杆，也可使用 WASD 或方向键控制"
        :style="{ width: DIAMETER + 'px', height: DIAMETER + 'px' }"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerCancel"
        @pointerleave="onPointerLeave"
        @contextmenu.prevent
      >
        <!-- 底图 -->
        <img
          :src="rouletteBottomUrl"
          alt=""
          aria-hidden="true"
          draggable="false"
          class="absolute inset-0 w-full h-full object-cover pointer-events-none select-none"
        />

        <!-- 扫描线 -->
        <div class="cp-scanline rounded-full"></div>
      </div>

      <!-- 拇指 (wheel-center 图片) — 放在 overflow-hidden 容器外，避免被裁剪 -->
      <img
        :src="wheelCenterUrl"
        alt=""
        aria-hidden="true"
        draggable="false"
        class="absolute pointer-events-none select-none
               transition-transform duration-75 ease-out"
        :style="{
          width: THUMB_NUB + 'px',
          height: THUMB_NUB + 'px',
          top: '50%',
          left: '50%',
          transform: `translate(calc(-50% + ${thumbVec.x * TRAVEL}px), calc(-50% + ${thumbVec.y * TRAVEL}px))`,
          opacity: active ? 1 : 0.85,
        }"
      />
    </div>

  </div>
</template>
