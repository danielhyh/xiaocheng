<script setup lang="ts">
/**
 * FuncButtons — 右侧功能按钮
 *
 * BRAKE: 紧急刹车
 * HORN: 鸣笛 (Phase 9)
 * 其余按钮标注对应 Phase,后续激活。
 */

import { onBeforeUnmount, ref } from 'vue'

const emit = defineEmits<{
  brake: []
  hornStart: []
  hornStop: []
  toggleAudioPanel: []
}>()

const buttons = [
  { icon: 'gimbal',  label: 'P4',  phase: 4, disabled: true  },
  { icon: 'light',   label: 'P8',  phase: 8, disabled: true  },
  { icon: 'nitro',   label: 'P10', phase: 10, disabled: true },
]

const BRAKE_REPEAT_MS = 100
const brakeTimer = ref<number | null>(null)

function startBrakeHold(e?: PointerEvent) {
  e?.currentTarget instanceof HTMLElement && e.currentTarget.setPointerCapture(e.pointerId)
  if (brakeTimer.value !== null) return

  emit('brake')
  brakeTimer.value = window.setInterval(() => emit('brake'), BRAKE_REPEAT_MS)
}

function stopBrakeHold() {
  if (brakeTimer.value === null) return

  window.clearInterval(brakeTimer.value)
  brakeTimer.value = null
}

onBeforeUnmount(stopBrakeHold)
</script>

<template>
  <div class="func-col">
    <!-- 刹车 -->
    <div class="func-item">
      <button
        class="fbtn brake"
        title="刹车"
        @pointerdown.prevent="startBrakeHold"
        @pointerup.prevent="stopBrakeHold"
        @pointercancel.prevent="stopBrakeHold"
        @pointerleave="stopBrakeHold"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="8"/>
          <path d="M12 7v6"/>
          <path d="M12 16h.01"/>
        </svg>
      </button>
      <span class="fbtn-lbl brake-lbl">BRAKE</span>
    </div>

    <!-- 鸣笛 (按住循环) -->
    <div class="func-item">
      <button
        class="fbtn horn"
        title="鸣笛 (按住)"
        @pointerdown.prevent="emit('hornStart')"
        @pointerup.prevent="emit('hornStop')"
        @pointerleave="emit('hornStop')"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/>
        </svg>
      </button>
      <span class="fbtn-lbl horn-lbl">HORN</span>
    </div>

    <!-- 音频面板切换 -->
    <div class="func-item">
      <button class="fbtn audio-toggle" title="音频控制" @click="emit('toggleAudioPanel')">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M11 5L6 9H2v6h4l5 4V5z"/>
          <path d="M15.5 8.5a5 5 0 0 1 0 7"/>
          <path d="M19 5a9 9 0 0 1 0 14"/>
        </svg>
      </button>
      <span class="fbtn-lbl audio-lbl">VOL</span>
    </div>

    <!-- 未激活按钮 -->
    <div v-for="btn in buttons" :key="btn.icon" class="func-item">
      <button class="fbtn" disabled :title="`Phase ${btn.phase}`">
        <!-- Gimbal -->
        <svg v-if="btn.icon === 'gimbal'" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>
        </svg>
        <!-- Light -->
        <svg v-else-if="btn.icon === 'light'" viewBox="0 0 24 24">
          <path d="M12 2a7 7 0 0 1 4 12.7V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.3A7 7 0 0 1 12 2z"/>
          <line x1="9" y1="21" x2="15" y2="21"/>
        </svg>
        <!-- Nitro -->
        <svg v-else-if="btn.icon === 'nitro'" viewBox="0 0 24 24">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </button>
      <span class="fbtn-lbl">{{ btn.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.func-col {
  position: absolute; right: 16px; top: 44px; bottom: 16px;
  width: 52px; z-index: 20;
  display: flex; flex-direction: column; align-items: center;
  justify-content: flex-end; gap: 8px;
}
.func-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.fbtn {
  width: 44px; height: 44px; border-radius: 12px;
  background: rgba(30, 34, 43, 0.85); border: 1px solid rgba(255,255,255,0.12);
  display: flex; align-items: center; justify-content: center;
  cursor: not-allowed; opacity: 0.45;
}
.fbtn svg {
  width: 20px; height: 20px; stroke: #8a8d95; fill: none;
  stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round;
}

/* 刹车 */
.fbtn.brake {
  cursor: pointer; opacity: 1;
  background: rgba(58, 21, 24, 0.9); border-color: rgba(255, 88, 88, 0.55);
}
.fbtn.brake:hover { background: #48191d; }
.fbtn.brake:active { transform: translateY(1px); }
.fbtn.brake svg { stroke: #ff6b6b; }
.brake-lbl { color: #ff6b6b; }

/* 鸣笛 */
.fbtn.horn {
  cursor: pointer; opacity: 1;
  background: rgba(44, 80, 132, 0.6); border-color: rgba(88, 166, 255, 0.45);
}
.fbtn.horn:hover { background: rgba(44, 80, 132, 0.8); }
.fbtn.horn:active { transform: translateY(1px); }
.fbtn.horn svg { stroke: #58a6ff; }
.horn-lbl { color: #58a6ff; }

/* 音频面板 */
.fbtn.audio-toggle {
  cursor: pointer; opacity: 1;
  background: rgba(30, 34, 43, 0.85); border-color: rgba(255,255,255,0.2);
}
.fbtn.audio-toggle:hover { background: rgba(50, 54, 63, 0.85); }
.fbtn.audio-toggle:active { transform: translateY(1px); }
.fbtn.audio-toggle svg { stroke: #e8e6e1; }
.audio-lbl { color: #8a8d95; }

.fbtn-lbl { font-size: 11px; color: #555860; }
</style>
