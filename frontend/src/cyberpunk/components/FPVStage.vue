<!--
  FPVStage — 中央 MJPEG 视频显示层 (R4)

  - 铺满主背景层, 位于所有控件之下
  - 左上角叠加 FPS + 分辨率小字
  - 加载失败: 离线占位 + 每 3000ms 重试
  - 叠加扫描线 + 十字准星, pointer-events: none
-->

<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'

const props = defineProps<{
  fps?: number | null
  resolution?: string | null
}>()

const streamUrl = computed(() => {
  const base = `${location.protocol}//${location.hostname}:${location.port || 8000}`
  return `${base}/stream/camera`
})

const imgKey = ref(0)
const hasError = ref(false)
const isLoading = ref(true)
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
  if (retryTimer !== null) return
  retryTimer = window.setTimeout(() => {
    retryTimer = null
    hasError.value = false
    isLoading.value = true
    imgKey.value++
  }, 3000)
}

onUnmounted(() => {
  if (retryTimer !== null) {
    window.clearTimeout(retryTimer)
    retryTimer = null
  }
})

// fps/resolution props 保留供将来使用，当前由 ReversePiP 组件显示
</script>

<template>
  <div class="absolute inset-0 z-0 overflow-hidden bg-hull-900">
    <!-- MJPEG 流 -->
    <img
      v-if="!hasError"
      :key="imgKey"
      :src="streamUrl"
      alt="FPV"
      class="w-full h-full object-cover select-none"
      draggable="false"
      @load="onLoad"
      @error="onError"
    />

    <!-- 离线占位 -->
    <div v-if="hasError"
         class="absolute inset-0 flex flex-col items-center justify-center gap-3
                bg-[radial-gradient(circle_at_center,rgba(52,224,255,0.12),rgba(5,7,12,0.95))]">
      <div class="w-20 h-20 rounded-full border-2 border-neon-cyan/60
                  flex items-center justify-center shadow-[0_0_18px_rgba(52,224,255,0.4)]">
        <div class="w-8 h-8 rounded-full border-2 border-neon-cyan/50"></div>
      </div>
      <div class="cp-display text-neon-cyan/80 tracking-[0.25em] text-sm">NO SIGNAL</div>
      <div class="cp-mono text-xs text-white/40">正在重试连接摄像头...</div>
    </div>

    <!-- 加载中 -->
    <div v-if="isLoading && !hasError"
         class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div class="w-8 h-8 rounded-full border-2 border-neon-cyan/30 border-t-neon-cyan animate-spin"></div>
    </div>

    <!-- FPS + 分辨率已移至 ReversePiP 组件上方显示 -->

    <!-- 扫描线 (混合模式叠加) -->
    <div class="absolute inset-0 pointer-events-none opacity-40 mix-blend-screen">
      <div class="absolute inset-0"
           :style="{
             backgroundImage: 'repeating-linear-gradient(to bottom, rgba(52,224,255,0.08) 0 2px, transparent 2px 4px)',
           }">
      </div>
      <div class="absolute inset-x-0 h-24 -top-24 animate-[scan-line_5s_linear_infinite]
                  bg-gradient-to-b from-transparent via-neon-cyan/25 to-transparent">
      </div>
    </div>

    <!-- 十字准星 + 四角框 -->
    <svg class="absolute inset-0 w-full h-full pointer-events-none opacity-35"
         preserveAspectRatio="none" viewBox="0 0 1000 500" aria-hidden="true">
      <g stroke="#34e0ff" stroke-width="1" fill="none" vector-effect="non-scaling-stroke">
        <line x1="500" y1="220" x2="500" y2="240"/>
        <line x1="500" y1="260" x2="500" y2="280"/>
        <line x1="460" y1="250" x2="480" y2="250"/>
        <line x1="520" y1="250" x2="540" y2="250"/>
        <circle cx="500" cy="250" r="3" fill="#34e0ff"/>
        <circle cx="500" cy="250" r="40" stroke-dasharray="3 5"/>
      </g>
      <g stroke="#34e0ff" stroke-width="2" fill="none" vector-effect="non-scaling-stroke" stroke-linecap="round">
        <polyline points="120,80 100,80 100,100"/>
        <polyline points="880,80 900,80 900,100"/>
        <polyline points="120,420 100,420 100,400"/>
        <polyline points="880,420 900,420 900,400"/>
      </g>
    </svg>
  </div>
</template>
