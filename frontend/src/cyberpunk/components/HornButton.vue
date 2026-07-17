<!--
  HornButton — HORN 按钮 (R8.4–R8.7)

  短按 (< 250ms)        → 发送 play { clip: 'horn' }
  长按 (≥ 250ms 跨阈值) → 阈值触发 hornStart, 抬起时 hornStop
-->

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import type { CommandBus } from '../composables/useCommandBus'
import hornBtnUrl from '../../assets/cyberpunk/horn-btn.png'

const props = defineProps<{ bus: CommandBus }>()

const HOLD_MS = 250

const pressed = ref(false)
const looping = ref(false)
let holdTimer: number | null = null

function clearHoldTimer() {
  if (holdTimer !== null) {
    window.clearTimeout(holdTimer)
    holdTimer = null
  }
}

function onDown(e: PointerEvent) {
  e.preventDefault()
  ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
  if (pressed.value) return
  pressed.value = true
  looping.value = false
  holdTimer = window.setTimeout(() => {
    looping.value = true
    props.bus.sendHornStart()
    holdTimer = null
  }, HOLD_MS)
}

function onUp() {
  if (!pressed.value) return
  pressed.value = false
  clearHoldTimer()
  if (looping.value) {
    looping.value = false
    props.bus.sendHornStop()
  } else {
    props.bus.sendHornShort()
  }
}

onBeforeUnmount(() => {
  clearHoldTimer()
  if (looping.value) {
    looping.value = false
    props.bus.sendHornStop()
  }
})
</script>

<template>
  <div class="relative flex flex-col items-center gap-0.5 select-none z-10">
    <button
      class="relative w-[64px] h-[64px] rounded-full
             transition-all duration-150 overflow-hidden"
      :class="{
        'scale-95 brightness-125': pressed,
        'ring-2 ring-neon-cyan/80 shadow-[0_0_12px_rgba(52,224,255,0.5)]': pressed || looping,
      }"
      @pointerdown="onDown"
      @pointerup="onUp"
      @pointercancel="onUp"
      @pointerleave="onUp"
      @contextmenu.prevent
      title="短按鸣笛 · 长按持续"
    >
      <img
        :src="hornBtnUrl"
        alt="鸣笛"
        draggable="false"
        class="absolute inset-0 w-full h-full object-contain pointer-events-none select-none"
      />
    </button>
    <span class="cp-display tracking-[0.2em] text-[9px] text-white/60">按住鸣笛</span>
  </div>
</template>
