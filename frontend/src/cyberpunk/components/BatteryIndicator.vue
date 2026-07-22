<!--
  BatteryIndicator — 电量格数显示 (R13)

  布局: [电池图标] 电压V | 百分比%  状态文字
  所有元素颜色统一由 battery_level 决定。

  格数映射 (4格):
    75-100%  → 4格   (ok)
    50-74%   → 3格   (ok)
    25-49%   → 2格   (low)
    5-24%    → 1格   (critical)
    <5%      → 0格   (critical, 闪烁)
-->

<script setup lang="ts">
import { computed } from 'vue'
import { useCarStore } from '../../stores/carStore'
import { mapBatteryLevel, TONE_COLOR } from '../utils/battery'
import batteryBgUrl from '../../assets/cyberpunk/battery-bar-bg.png'

const store = useCarStore()

const view = computed(() => mapBatteryLevel(store.sensors.battery_level))
const color = computed(() => TONE_COLOR[view.value.tone])

// 格数计算
const bars = computed(() => {
  const pct = store.sensors.battery_percent
  if (typeof pct !== 'number' || !Number.isFinite(pct) || pct < 5) return 0
  if (pct < 25) return 1
  if (pct < 50) return 2
  if (pct < 75) return 3
  return 4
})

// 电压显示 (保留1位小数)
const voltageText = computed(() => {
  const v = store.sensors.battery_voltage
  if (typeof v !== 'number' || !Number.isFinite(v) || v <= 0) return '--'
  return v.toFixed(1)
})

// 百分比显示
const percentText = computed(() => {
  const pct = store.sensors.battery_percent
  if (typeof pct !== 'number' || !Number.isFinite(pct)) return '--'
  return Math.round(pct)
})

const TOTAL_BARS = 4
</script>

<template>
  <div
    class="relative flex items-center gap-2 px-4 py-1 h-[30px]"
    :class="{ 'cp-breathe-critical': view.blink }"
  >
    <!-- 背景图 -->
    <img
      :src="batteryBgUrl"
      alt=""
      aria-hidden="true"
      draggable="false"
      class="absolute inset-0 w-full h-full object-fill pointer-events-none select-none"
    />
    <!-- 电池图标 (圆角外壳 + 格子) -->
    <span
      class="relative z-10 inline-flex items-center w-[38px] h-[18px] rounded-[4px] border-[1.5px] mr-[4px]"
      :style="{ borderColor: color }"
    >
      <!-- 格子容器 -->
      <span class="flex items-center gap-[2px] px-[2.5px] py-[2px] w-full h-full">
        <span
          v-for="i in TOTAL_BARS"
          :key="i"
          class="flex-1 h-full rounded-[2px] transition-all duration-300"
          :style="{
            background: i <= bars ? color : 'transparent',
            boxShadow: i <= bars ? `0 0 4px ${color}66` : 'none',
          }"
        ></span>
      </span>
      <!-- 正极凸起 -->
      <span
        class="absolute -right-[5px] top-1/2 -translate-y-1/2 w-[3px] h-[8px] rounded-r-[2px]"
        :style="{ background: color }"
      ></span>
    </span>

    <!-- 电压 -->
    <span
      class="relative z-10 cp-display text-xs font-normal tracking-wide"
      :style="{ color, textShadow: `0 0 6px ${color}55` }"
    >
      {{ voltageText }}V
    </span>

    <!-- 分隔线 -->
    <span
      class="relative z-10 w-[1px] h-3 opacity-50"
      :style="{ background: color }"
    ></span>

    <!-- 百分比 -->
    <span
      class="relative z-10 cp-display text-xs font-normal tracking-wide"
      :style="{ color, textShadow: `0 0 6px ${color}55` }"
    >
      {{ percentText }}%
    </span>

    <!-- 状态文字 -->
    <span
      class="relative z-10 cp-display text-xs font-normal tracking-wider ml-1"
      :style="{ color, textShadow: `0 0 8px ${color}66` }"
    >
      {{ view.text }}
    </span>
  </div>
</template>

<style scoped>
@keyframes cp-breathe-critical {
  0%, 100% { filter: drop-shadow(0 0 6px rgba(255, 58, 74, 0.55)); opacity: 1; }
  50%      { filter: drop-shadow(0 0 18px rgba(255, 58, 74, 0.9));  opacity: 0.55; }
}
.cp-breathe-critical {
  animation: cp-breathe-critical 0.8s ease-in-out infinite;
}
</style>
