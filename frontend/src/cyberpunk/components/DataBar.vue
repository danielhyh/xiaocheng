<!--
  DataBar — 底部数据条 (R14, 按提示词简化)

  只展示核心三项: 当前速度 / 累计里程 / 云台角度 (Pan & Tilt)
  字段为 null / undefined 时显示 "--"
  固定底部中央 + 半透明霓虹描边
-->

<script setup lang="ts">
import { computed } from 'vue'
import { useCarStore } from '../../stores/carStore'
import { fmtNum } from '../utils/format'
import dashboardBgUrl from '../../assets/cyberpunk/data-bar-bg.png'

const store = useCarStore()

// 当前速度: 从 tel.motion.speed 取值 (单位 m/s, 后端约定)
const speedText = computed(() => {
  const s = store.motion.speed
  if (s === null || s === undefined || !Number.isFinite(s)) return '--'
  return `${fmtNum(s, 1)}m/s`
})

// 累计里程: 后端暂未推送, 保留占位; 如果后续后端加了 odo 字段, 改这里即可
const odometerText = computed(() => {
  // 目前 carStore 未定义 odometer, 读取 motion 兜底字段
  const odo = (store.motion as any).odometer
  if (odo === null || odo === undefined || !Number.isFinite(odo)) return '--'
  return `${Number(odo).toFixed(1)}km`
})

const panText = computed(() => {
  const p = store.sensors.gimbal_pan
  if (p === null || p === undefined || !Number.isFinite(p)) return '--'
  // 把 0-180 的舵机角度映射到 -90 ~ +90 相对中位 (更直观)
  return `${Math.round(p - 90)}°`
})

const tiltText = computed(() => {
  const t = store.sensors.gimbal_tilt
  if (t === null || t === undefined || !Number.isFinite(t)) return '--'
  return `${Math.round(t - 90)}°`
})
</script>

<template>
  <footer class="absolute bottom-3 left-1/2 -translate-x-1/2 z-20
                 flex items-center
                 cp-mono text-[11px] text-white/80
                 databar-container">
    <!-- 背景图 -->
    <img
      :src="dashboardBgUrl"
      alt=""
      aria-hidden="true"
      draggable="false"
      class="absolute inset-0 w-full h-full object-fill pointer-events-none select-none"
    />

    <!-- 速度 -->
    <span class="relative z-10 databar-cell">
      <span class="text-white/45 databar-label">速度</span>
      <span class="text-neon-cyan font-semibold databar-num">{{ speedText }}</span>
    </span>

    <span class="relative z-10 w-px h-3 bg-neon-cyan/30 flex-shrink-0"></span>

    <!-- 里程 -->
    <span class="relative z-10 databar-cell">
      <span class="text-white/45 databar-label">里程</span>
      <span class="text-neon-green font-semibold databar-num">{{ odometerText }}</span>
    </span>

    <span class="relative z-10 w-px h-3 bg-neon-cyan/30 flex-shrink-0"></span>

    <!-- 云台角度 -->
    <span class="relative z-10 databar-cell">
      <span class="text-white/45 databar-label--short">P:</span>
      <span class="text-neon-amber font-semibold databar-num--short">{{ panText }}</span>
      <span class="text-white/45 databar-label--short ml-3">T:</span>
      <span class="text-neon-amber font-semibold databar-num--short">{{ tiltText }}</span>
    </span>
  </footer>
</template>

<style scoped>
.databar-container {
  width: 300px;
  height: 34px;
  padding: 0 12px;
}

/* 每个数据段固定宽度等分, 标签左对齐 + 数值右对齐 */
.databar-cell {
  display: flex;
  align-items: center;
  flex: 1 1 0;
  min-width: 0;
  padding: 0 6px;
}

/* 标签固定宽度, 左对齐不动 */
.databar-label {
  display: inline-block;
  width: 2em;
  flex-shrink: 0;
  text-align: left;
}

.databar-label--short {
  display: inline-block;
  width: 1.4em;
  flex-shrink: 0;
  text-align: left;
}

/* 数字固定宽度右对齐, 位数变化不影响标签位置 */
.databar-num {
  display: inline-block;
  width: 5ch;
  flex-shrink: 0;
  text-align: right;
  font-variant-numeric: tabular-nums;
  margin-left: 6px;
}

.databar-num--short {
  display: inline-block;
  width: 3ch;
  flex-shrink: 0;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
</style>
