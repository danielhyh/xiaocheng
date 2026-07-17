<!--
  BrakeButton — BRAKE 按钮 (R8.1–R8.3)

  按住: 100 ± 20ms 循环发送 cmd.brake, 首帧 ≤ 20ms 内
  释放: 立即停止发送
-->

<script setup lang="ts">
import { ref } from 'vue'
import { useKeepaliveSender } from '../composables/useKeepaliveSender'
import type { CommandBus } from '../composables/useCommandBus'
import brakeBtnUrl from '../../assets/cyberpunk/brake-btn.png'

const props = defineProps<{ bus: CommandBus }>()
const emit = defineEmits<{ press: [] }>()

const pressed = ref(false)

const sender = useKeepaliveSender<null>({
  emit: () => props.bus.sendBrake(),
  periodMs: 100,
})

function onDown(e: PointerEvent) {
  e.preventDefault()
  ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
  if (pressed.value) return
  pressed.value = true
  emit('press')
  sender.start(null)
}

function onUp() {
  if (!pressed.value) return
  pressed.value = false
  sender.stop()
}
</script>

<template>
  <div class="relative flex flex-col items-center gap-0.5 select-none z-10">
    <button
      class="relative w-[64px] h-[64px] rounded-full
             transition-transform overflow-hidden"
      :class="{ 'scale-95 brightness-125': pressed }"
      @pointerdown="onDown"
      @pointerup="onUp"
      @pointercancel="onUp"
      @pointerleave="onUp"
      @contextmenu.prevent
    >
      <img
        :src="brakeBtnUrl"
        alt="BRAKE"
        draggable="false"
        class="absolute inset-0 w-full h-full object-contain pointer-events-none select-none"
      />
      <span
        class="absolute inset-0 rounded-full pointer-events-none"
        :class="pressed ? 'animate-ping bg-neon-red/15' : ''"
      ></span>
    </button>
  </div>
</template>
