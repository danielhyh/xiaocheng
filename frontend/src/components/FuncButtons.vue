<script setup lang="ts">
/**
 * FuncButtons — 右侧功能按钮
 *
 * BRAKE: 紧急刹车
 * HORN: 鸣笛 — 点按响一声,按住循环响
 * VOL: 音频面板
 * LIGHT: 灯光面板
 * GIMBAL: 云台面板
 * NITRO: 氮气加速
 */

import { onBeforeUnmount, ref } from 'vue'

const emit = defineEmits<{
  brake: []
  horn: []
  hornStart: []
  hornStop: []
  toggleAudioPanel: []
  toggleLightPanel: []
  toggleGimbalPanel: []
  nitro: []
}>()

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

// ---- 鸣笛: 短按响一声,长按循环 ----
const HORN_HOLD_THRESHOLD = 250
let hornDownAt = 0
let hornHoldTimer: number | null = null
let hornIsLooping = false

function onHornDown(e?: PointerEvent) {
  e?.currentTarget instanceof HTMLElement && e.currentTarget.setPointerCapture(e.pointerId)
  hornDownAt = Date.now()
  hornIsLooping = false

  hornHoldTimer = window.setTimeout(() => {
    hornIsLooping = true
    emit('hornStart')
  }, HORN_HOLD_THRESHOLD)
}

function onHornUp() {
  if (hornDownAt === 0) return

  if (hornHoldTimer !== null) {
    window.clearTimeout(hornHoldTimer)
    hornHoldTimer = null
  }

  if (hornIsLooping) {
    emit('hornStop')
    hornIsLooping = false
  } else {
    emit('horn')
  }
  hornDownAt = 0
}

onBeforeUnmount(() => {
  stopBrakeHold()
  if (hornHoldTimer !== null) {
    window.clearTimeout(hornHoldTimer)
    hornHoldTimer = null
  }
  if (hornIsLooping) {
    emit('hornStop')
    hornIsLooping = false
  }
})
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
        @contextmenu.prevent
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="8"/>
          <path d="M12 7v6"/>
          <path d="M12 16h.01"/>
        </svg>
      </button>
      <span class="fbtn-lbl brake-lbl">BRAKE</span>
    </div>

    <!-- 鸣笛 -->
    <div class="func-item">
      <button
        class="fbtn horn"
        title="鸣笛"
        @pointerdown.prevent="onHornDown"
        @pointerup.prevent="onHornUp"
        @pointercancel.prevent="onHornUp"
        @pointerleave="onHornUp"
        @contextmenu.prevent
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/>
        </svg>
      </button>
      <span class="fbtn-lbl horn-lbl">HORN</span>
    </div>

    <!-- 音频面板 -->
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

    <!-- 灯光面板 -->
    <div class="func-item">
      <button class="fbtn light-toggle" title="灯光控制" @click="emit('toggleLightPanel')">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 2a7 7 0 0 1 4 12.7V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.3A7 7 0 0 1 12 2z"/>
          <line x1="9" y1="21" x2="15" y2="21"/>
        </svg>
      </button>
      <span class="fbtn-lbl light-lbl">LIGHT</span>
    </div>

    <!-- 云台面板 (Phase 4) -->
    <div class="func-item">
      <button class="fbtn gimbal-toggle" title="云台控制" @click="emit('toggleGimbalPanel')">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>
        </svg>
      </button>
      <span class="fbtn-lbl gimbal-lbl">GIMBAL</span>
    </div>

    <!-- 氮气加速 (Phase 10) -->
    <div class="func-item">
      <button class="fbtn nitro-btn" title="氮气加速" @click="emit('nitro')">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </button>
      <span class="fbtn-lbl nitro-lbl">NITRO</span>
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
  cursor: pointer; opacity: 1;
}
.fbtn svg {
  width: 20px; height: 20px; stroke: #8a8d95; fill: none;
  stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round;
}
.fbtn:hover { background: rgba(40, 44, 53, 0.85); }
.fbtn:active { transform: translateY(1px); }

/* 刹车 */
.fbtn.brake {
  background: rgba(58, 21, 24, 0.9); border-color: rgba(255, 88, 88, 0.55);
}
.fbtn.brake:hover { background: #48191d; }
.fbtn.brake svg { stroke: #ff6b6b; }
.brake-lbl { color: #ff6b6b; }

/* 鸣笛 */
.fbtn.horn {
  background: rgba(44, 80, 132, 0.6); border-color: rgba(88, 166, 255, 0.45);
}
.fbtn.horn:hover { background: rgba(44, 80, 132, 0.8); }
.fbtn.horn svg { stroke: #58a6ff; }
.horn-lbl { color: #58a6ff; }

/* 音频面板 */
.fbtn.audio-toggle {
  background: rgba(30, 34, 43, 0.85); border-color: rgba(255,255,255,0.2);
}
.fbtn.audio-toggle:hover { background: rgba(50, 54, 63, 0.85); }
.fbtn.audio-toggle svg { stroke: #e8e6e1; }
.audio-lbl { color: #8a8d95; }

/* 灯光面板 */
.fbtn.light-toggle {
  background: rgba(60, 50, 20, 0.7); border-color: rgba(255, 200, 50, 0.4);
}
.fbtn.light-toggle:hover { background: rgba(70, 60, 25, 0.8); }
.fbtn.light-toggle svg { stroke: #ffc832; fill: none; }
.light-lbl { color: #ffc832; }

/* 云台面板 */
.fbtn.gimbal-toggle {
  background: rgba(20, 60, 50, 0.7); border-color: rgba(45, 210, 132, 0.4);
}
.fbtn.gimbal-toggle:hover { background: rgba(25, 70, 60, 0.8); }
.fbtn.gimbal-toggle svg { stroke: #2dd284; }
.gimbal-lbl { color: #2dd284; }

/* 氮气加速 */
.fbtn.nitro-btn {
  background: rgba(80, 40, 10, 0.7); border-color: rgba(255, 140, 0, 0.5);
}
.fbtn.nitro-btn:hover { background: rgba(100, 50, 15, 0.8); }
.fbtn.nitro-btn svg { stroke: #ff8c00; fill: rgba(255, 140, 0, 0.2); }
.nitro-lbl { color: #ff8c00; }

.fbtn-lbl { font-size: 11px; color: #555860; }
</style>
