<!--
  HUDBar — 顶部状态条 (R3)

  字段 (按提示词):
    - 左: 电量 + 电压 + 百分比 + 状态文字
    - 中: 模式切换 (手动/智能)
    - 右: 连接点 + 延迟(ms) + CPU(°C)
  FPS/分辨率在 FPVStage 左上角画面内叠加, 不放这里。
-->

<script setup lang="ts">
import { computed } from 'vue'
import { useCarStore } from '../../stores/carStore'
import BatteryIndicator from './BatteryIndicator.vue'
import ModeSwitch from './ModeSwitch.vue'
import type { CommandBus } from '../composables/useCommandBus'
import { fmtLatency, fmtTemp } from '../utils/format'
import statusBgUrl from '../../assets/cyberpunk/status-bar-bg.png'

const props = defineProps<{
  bus: CommandBus
}>()

const store = useCarStore()

/** 状态分级颜色 */
const COLOR_GREEN = '#2dff88'
const COLOR_YELLOW = '#ffd23a'
const COLOR_RED = '#ff3a4a'

const latencyText = computed(() =>
  fmtLatency(store.wsLatency, !store.connected),
)

// 延迟颜色: ≤80ms 绿, 80~200 黄, >200 红
const latencyColor = computed(() => {
  if (!store.connected) return COLOR_RED
  const ms = store.wsLatency
  if (ms === null || ms === undefined) return COLOR_RED
  if (ms <= 80) return COLOR_GREEN
  if (ms <= 200) return COLOR_YELLOW
  return COLOR_RED
})

// CPU 温度颜色: ≤60°C 绿, 60~75 黄, >75 红
const cpuColor = computed(() => {
  const temp = store.sensors.cpu_temp
  if (temp === null || temp === undefined || !Number.isFinite(temp)) return COLOR_GREEN
  if (temp <= 60) return COLOR_GREEN
  if (temp <= 75) return COLOR_YELLOW
  return COLOR_RED
})
</script>

<template>
  <header class="hud-header absolute top-0 left-0 right-0 z-[3] h-11 px-5
                 flex items-center justify-between">
    <!-- 左: 电池 (图标+电压+百分比+档位 已集成在组件内) -->
    <div class="hud-side hud-side--left flex items-center ml-2 mt-2">
      <BatteryIndicator />
    </div>

    <!-- 中: 模式切换 (绝对定位居中, 不受 flex justify-between 影响) -->
    <div class="absolute left-1/2 top-0 -translate-x-1/2 z-[2]">
      <ModeSwitch :bus="bus" />
    </div>

    <!-- 右: 连接 + 延迟 + CPU (固定宽度背景板) -->
    <div class="hud-side hud-side--right relative flex items-center gap-3 text-xs mr-2 mt-2 px-4 py-2">
      <!-- 背景图 -->
      <img
        :src="statusBgUrl"
        alt=""
        aria-hidden="true"
        draggable="false"
        class="absolute inset-0 w-full h-full object-fill pointer-events-none select-none"
      />

      <!-- 连接点 -->
      <span class="relative z-10 flex items-center gap-1">
        <span
          class="inline-block w-1.5 h-1.5 rounded-full"
          :class="store.connected
            ? 'bg-neon-green shadow-[0_0_8px_#2dff88]'
            : 'bg-neon-red shadow-[0_0_8px_#ff3a4a] animate-pulse'"
        ></span>
        <span
          class="cp-display text-xs font-normal tracking-wide hud-num-status"
          :style="{ color: store.connected ? COLOR_GREEN : COLOR_RED, textShadow: `0 0 6px ${store.connected ? COLOR_GREEN : COLOR_RED}55` }"
        >
          {{ store.connected ? '已连接' : '未连接' }}
        </span>
      </span>

      <!-- 延迟: wifi 图标 + ms -->
      <span class="relative z-10 flex items-center gap-1">
        <svg width="13" height="12" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
             :style="{ color: latencyColor }">
          <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
          <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
          <line x1="12" y1="20" x2="12" y2="20"/>
        </svg>
        <span
          class="cp-display text-xs font-normal hud-num"
          :style="{ color: latencyColor, textShadow: `0 0 6px ${latencyColor}55` }"
        >{{ latencyText }}</span>
      </span>

      <!-- CPU 温度: cpu 图标 + °C -->
      <span class="relative z-10 flex items-center gap-1">
        <svg width="13" height="12" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
             :style="{ color: cpuColor }">
          <rect x="4" y="4" width="16" height="16" rx="2"/>
          <rect x="9" y="9" width="6" height="6"/>
          <line x1="9" y1="1" x2="9" y2="4"/>
          <line x1="15" y1="1" x2="15" y2="4"/>
          <line x1="9" y1="20" x2="9" y2="23"/>
          <line x1="15" y1="20" x2="15" y2="23"/>
          <line x1="20" y1="9" x2="23" y2="9"/>
          <line x1="20" y1="14" x2="23" y2="14"/>
          <line x1="1" y1="9" x2="4" y2="9"/>
          <line x1="1" y1="14" x2="4" y2="14"/>
        </svg>
        <span
          class="cp-display text-xs font-normal hud-num"
          :style="{ color: cpuColor, textShadow: `0 0 6px ${cpuColor}55` }"
        >{{ fmtTemp(store.sensors.cpu_temp) }}</span>
      </span>
    </div>

    <!-- 底部赛博朋克线条 — 左段 -->
    <div class="hud-line hud-line--left"></div>
    <!-- 底部赛博朋克线条 — 右段 -->
    <div class="hud-line hud-line--right"></div>
  </header>
</template>

<style scoped>
.hud-header {
  background: rgba(0, 0, 0, 0.6);
}

/* 左右区域 */
.hud-side {
  flex-shrink: 0;
}

/* 左侧固定宽度: 按最大内容 "8.4V | 100% 电量不足" 计算 */
.hud-side--left {
  width: 220px;
}

/* 右侧固定宽度: 按最大内容 "未连接 460ms 99°C" 计算 */
.hud-side--right {
  width: 220px;
  justify-content: space-between;
}

/* 数字固定宽度, 防止内容变化导致布局跳动 */
.hud-num {
  display: inline-block;
  min-width: 4ch;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* 连接状态文字固定宽度 (已连接/未连接 都是3个中文字) */
.hud-num-status {
  display: inline-block;
  min-width: 3em;
  text-align: center;
}

/* 底线通用 */
.hud-line {
  position: absolute;
  bottom: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(52, 224, 255, 0.2) 20%,
    rgba(52, 224, 255, 0.45) 80%,
    transparent 100%
  );
  box-shadow: 0 0 4px rgba(52, 224, 255, 0.25);
  pointer-events: none;
}

.hud-line--left {
  left: 0;
  right: calc(50% + 95px);
}

.hud-line--right {
  left: calc(50% + 95px);
  right: 0;
}
</style>
