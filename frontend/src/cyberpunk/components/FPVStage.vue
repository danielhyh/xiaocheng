<!--
  FPVStage — 中央前置主摄预留层 (R4)

  - 当前后置摄像头画面由 ReversePiP 显示
  - 中央区域预留给未来前置主摄像头
  - 叠加扫描线 + 十字准星, pointer-events: none
-->

<script setup lang="ts">
defineProps<{
  fps?: number | null
  resolution?: string | null
}>()
</script>

<template>
  <div class="absolute inset-0 z-0 overflow-hidden bg-hull-900">
    <!-- 前置主摄像头预留占位 -->
    <div class="absolute inset-0 flex flex-col items-center justify-center gap-3
                bg-[radial-gradient(circle_at_center,rgba(52,224,255,0.10),rgba(5,7,12,0.98))]">
      <div class="w-20 h-20 rounded-full border-2 border-neon-cyan/60
                  flex items-center justify-center shadow-[0_0_18px_rgba(52,224,255,0.4)]">
        <div class="w-8 h-8 rounded-full border-2 border-neon-cyan/50"></div>
      </div>
      <div class="cp-display text-neon-cyan/80 tracking-[0.25em] text-sm">FRONT CAMERA STANDBY</div>
      <div class="cp-mono text-xs text-white/40">前置主摄像头未接入</div>
    </div>

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
