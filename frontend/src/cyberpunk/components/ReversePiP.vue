<!--
  ReversePiP — 倒车画中画 (R5)

  默认: 缩略 (≤ 25% 视口宽度)
  motion.vy < 0: 自动放大 (≥ 40% 视口宽度)
  右下角手动放大/缩小按钮
  fps/分辨率显示在组件上方
  背景: rear-view_fixed.png 赛博朋克边框图
-->

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useCarStore } from '../../stores/carStore'
import rearViewUrl from '../../assets/cyberpunk/rear-view-border.png'

const props = defineProps<{
  fps?: number | null
  resolution?: string | null
}>()

const store = useCarStore()

// 自动放大: 倒车时
const autoEnlarged = computed(() => (store.motion.vy ?? 0) < 0)
// 手动放大状态
const manualEnlarged = ref(false)

const enlarged = computed(() => autoEnlarged.value || manualEnlarged.value)

function toggleSize() {
  manualEnlarged.value = !manualEnlarged.value
}

const fpsText = computed(() =>
  props.fps == null ? '--fps' : `${Math.round(props.fps)}fps`,
)
const resText = computed(() => props.resolution ?? '--')
</script>

<template>
  <!-- PiP 主体 (包含 fps/分辨率行)
       top: HUD(44px) + fps行高(14px) + 间距(4px) = 62px -->
  <div
    class="absolute top-[62px] left-4 z-20 transition-all duration-300 ease-out overflow-visible"
    :style="{
      width: enlarged ? '30vw' : '18vw',
      maxWidth: enlarged ? '340px' : '190px',
      aspectRatio: '16 / 9',
    }"
  >
    <!-- fps/分辨率 — 紧贴在 PiP 上方，固定偏移不随放大变动 -->
    <div class="absolute bottom-full left-[15px] mb-[3px] pointer-events-none
                flex items-center gap-2 cp-mono text-[10px]
                text-white/80 drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)]">
      <span class="flex items-center gap-1">
        <span class="w-1 h-1 rounded-full bg-neon-cyan shadow-[0_0_5px_#34e0ff]"></span>
        <span class="text-neon-cyan">{{ fpsText }}</span>
      </span>
      <span class="text-white/45">{{ resText }}</span>
    </div>
    <!-- 赛博朋克边框背景图 (铺满, 不裁剪) — 需要单独的 overflow-hidden 容器 -->
    <div class="absolute inset-0 overflow-hidden rounded-sm">
      <img
        :src="rearViewUrl"
        alt=""
        aria-hidden="true"
        draggable="false"
        class="absolute inset-0 w-full h-full select-none pointer-events-none"
        style="object-fit: fill;"
      />
    </div>

    <!-- 内容区域 (留出边框视觉空间) -->
    <div class="absolute inset-[6%]">
      <!-- 扫描线叠加 -->
      <div class="absolute inset-0 opacity-25 mix-blend-screen pointer-events-none"
           :style="{
             backgroundImage: 'repeating-linear-gradient(to bottom, rgba(158,204,253,0.12) 0 2px, transparent 2px 4px)',
           }">
      </div>
    </div>

    <!-- 左上: REAR 标识 -->
    <div class="absolute top-[8%] left-[6%] cp-display tracking-[0.2em] font-bold
                drop-shadow-[0_0_8px_rgba(158,204,253,0.8)]"
         :style="{ fontSize: enlarged ? '13px' : '9px', color: '#9ECCFD' }">
      REAR
    </div>

    <!-- 右上: REC 指示 (倒车时) -->
    <div v-if="autoEnlarged"
         class="absolute top-[8%] right-[6%] flex items-center gap-1 cp-mono text-white/70"
         :style="{ fontSize: enlarged ? '10px' : '8px' }">
      <span class="w-1.5 h-1.5 rounded-full bg-neon-red shadow-[0_0_6px_#ff3a4a] animate-pulse"></span>
      <span>REC</span>
    </div>

    <!-- 右下: 手动放大/缩小按钮 -->
    <button
      class="absolute bottom-[8%] right-[6%] flex items-center justify-center
             rounded cursor-pointer transition-all duration-150
             border border-[#9ECCFD]/40 bg-black/50
             hover:bg-[#9ECCFD]/15 hover:border-[#9ECCFD]/70
             active:scale-90"
      :style="{
        width: enlarged ? '28px' : '20px',
        height: enlarged ? '28px' : '20px',
      }"
      :title="enlarged ? '缩小' : '放大'"
      @click.stop="toggleSize"
    >
      <!-- 放大图标 -->
      <svg v-if="!enlarged"
           :width="enlarged ? 14 : 10" :height="enlarged ? 14 : 10"
           viewBox="0 0 24 24" fill="none" stroke="#9ECCFD" stroke-width="2.5"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline points="15 3 21 3 21 9"/>
        <polyline points="9 21 3 21 3 15"/>
        <line x1="21" y1="3" x2="14" y2="10"/>
        <line x1="3" y1="21" x2="10" y2="14"/>
      </svg>
      <!-- 缩小图标 -->
      <svg v-else
           :width="enlarged ? 14 : 10" :height="enlarged ? 14 : 10"
           viewBox="0 0 24 24" fill="none" stroke="#9ECCFD" stroke-width="2.5"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline points="4 14 10 14 10 20"/>
        <polyline points="20 10 14 10 14 4"/>
        <line x1="10" y1="14" x2="3" y2="21"/>
        <line x1="21" y1="3" x2="14" y2="10"/>
      </svg>
    </button>
  </div>
</template>
