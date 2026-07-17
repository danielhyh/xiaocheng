<!--
  ModeSwitch — 模式切换控件 (R12)

  两档: 手动 / 智能
    - 手动 → cmd.mode { mode: "manual" }
    - 智能 → cmd.mode { mode: "avoid" }  (后端当前已实现的非手动模式)
  视觉数据源唯一: CarStore.mode

  样式: 整体梯形, 中间截断为左右对称半梯形
-->

<script setup lang="ts">
import { computed } from 'vue'
import { useCarStore } from '../../stores/carStore'
import type { CommandBus } from '../composables/useCommandBus'
import topBarBg from '../../assets/cyberpunk/mode-switch-bg.png'

const props = defineProps<{ bus: CommandBus }>()

const store = useCarStore()

const SMART_MODE = 'avoid'  // 当前"智能"对应后端 AVOID

const isManual = computed(() => store.mode === 'manual')
const isSmart = computed(() => store.mode !== 'manual')

function selectManual() {
  if (store.mode === 'manual') return
  props.bus.sendMode('manual')
}
function selectSmart() {
  if (store.mode !== 'manual') return
  props.bus.sendMode(SMART_MODE)
}
</script>

<template>
  <div class="mode-switch-wrapper">
    <!-- 梯形底图 -->
    <div class="mode-switch-bg">
      <img :src="topBarBg" alt="" class="mode-switch-bg-img" />
    </div>
    <!-- 按钮区域: 左半梯形 + 右半梯形 -->
    <div class="mode-switch-buttons">
      <button
        class="mode-btn mode-btn--left"
        :class="{ 'mode-btn--active': isManual }"
        @click="selectManual"
      >
        手动
      </button>
      <button
        class="mode-btn mode-btn--right"
        :class="{ 'mode-btn--active': isSmart }"
        @click="selectSmart"
      >
        智能
      </button>
    </div>
  </div>
</template>

<style scoped>
.mode-switch-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 240px;
  height: 50px;
}

.mode-switch-bg {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.mode-switch-bg-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  pointer-events: none;
}

.mode-switch-buttons {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  /* 中间留 2px 间隙模拟截断线 */
  gap: 2px;
  padding: 0 28px;
  width: 100%;
  justify-content: center;
}

.mode-btn {
  position: relative;
  height: 28px;
  flex: 1;
  max-width: 100px;
  border: 1px solid rgba(52, 224, 255, 0.25);
  background: rgba(22, 34, 52, 0.75);
  color: rgba(255, 255, 255, 0.55);
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.12em;
  cursor: pointer;
  transition: all 0.2s ease;
}

/* 左按钮: 梯形左半 — 左边斜切, 右边垂直 */
.mode-btn--left {
  clip-path: polygon(10% 0%, 100% 0%, 100% 100%, 0% 100%);
  border-radius: 4px;
}

/* 右按钮: 梯形右半 — 左边垂直, 右边斜切 */
.mode-btn--right {
  clip-path: polygon(0% 0%, 90% 0%, 100% 100%, 0% 100%);
  border-radius: 4px;
}

.mode-btn:hover:not(.mode-btn--active) {
  color: rgba(255, 255, 255, 0.8);
  background: rgba(52, 224, 255, 0.08);
}

.mode-btn--active {
  color: #ffffff;
  border-color: rgba(52, 224, 255, 0.8);
  background: linear-gradient(
    180deg,
    rgba(52, 224, 255, 0.3) 0%,
    rgba(52, 224, 255, 0.08) 100%
  );
  box-shadow:
    0 0 12px rgba(52, 224, 255, 0.5),
    inset 0 0 10px rgba(52, 224, 255, 0.2),
    0 0 2px rgba(52, 224, 255, 0.8);
  text-shadow: 0 0 8px rgba(52, 224, 255, 0.7);
}
</style>
