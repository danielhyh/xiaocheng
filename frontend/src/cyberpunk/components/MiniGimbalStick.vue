<!--
  MiniGimbalStick — 右下角的小型云台双轴摇杆

  - 外圆直径 80px (比左下的 MoveJoystick 小一圈, 适合右手拇指末端轻推)
  - 四向箭头指示 Pan/Tilt
  - 100ms 保活, 释放立即停发 (R7)
  - 双击回中
-->

<script setup lang="ts">
import { computed, ref } from 'vue'
import { normalizeOffset } from '../utils/joystick'
import { useKeepaliveSender } from '../composables/useKeepaliveSender'
import type { CommandBus, GimbalVec } from '../composables/useCommandBus'
import gimbalBaseUrl from '../../assets/cyberpunk/gimbal-base.png'
import gimbalThumbUrl from '../../assets/cyberpunk/gimbal-thumb.png'

const props = defineProps<{ bus: CommandBus }>()

const DIAMETER = 70
const RADIUS = DIAMETER / 2
const THUMB_NUB = 28
const THUMB_NUB_R = THUMB_NUB / 2
// 拇指边缘刚好卡在轮盘边界：行程 = 轮盘半径 - 拇指半径
const TRAVEL = RADIUS - THUMB_NUB_R
const DEADZONE = 0.08

const baseEl = ref<HTMLDivElement>()
const thumbVec = ref({ x: 0, y: 0 })
const active = ref(false)

const sender = useKeepaliveSender<GimbalVec>({
  emit: (p) => {
    if (Math.abs(p.pan) < DEADZONE && Math.abs(p.tilt) < DEADZONE) return
    props.bus.sendGimbal(p.pan, p.tilt)
  },
  periodMs: 100,
})

const currentPayload = computed<GimbalVec>(() => ({
  pan: Number(thumbVec.value.x.toFixed(3)),
  tilt: Number((-thumbVec.value.y).toFixed(3)),
}))

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
  sender.stop()
}

function onCenter() {
  release()
  props.bus.sendGimbalCenter()
}
</script>

<template>
  <div class="relative flex flex-col items-center gap-0.5 select-none z-10">
    <div class="relative rounded-full p-[2px]">
      <div
        ref="baseEl"
        class="relative rounded-full touch-none overflow-hidden"
        :style="{ width: DIAMETER + 'px', height: DIAMETER + 'px' }"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="release"
        @pointercancel="release"
        @pointerleave="active && release()"
        @dblclick.prevent="onCenter"
        @contextmenu.prevent
        title="拖动控制云台, 双击回中"
      >
        <!-- 底图 -->
        <img
          :src="gimbalBaseUrl"
          alt=""
          aria-hidden="true"
          draggable="false"
          class="absolute inset-0 w-full h-full object-cover pointer-events-none select-none"
        />
      </div>

      <!-- 拇指 — 放在 overflow-hidden 容器外，行程限制在轮盘内 -->
      <img
        :src="gimbalThumbUrl"
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

    <span class="cp-display tracking-[0.2em] text-[9px] text-white/60">云台控制</span>
  </div>
</template>
