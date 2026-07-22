<!--
  FloatingActionGroup — 右侧悬浮 2 按钮 (灯光/音频)
  高亮态纯 CSS filter 实现，不额外包裹 div
-->

<script setup lang="ts">
import { computed } from 'vue'
import type { CommandBus } from '../composables/useCommandBus'
import iconLightUrl from '../../assets/cyberpunk/icon-light.png'
import iconSoundUrl from '../../assets/cyberpunk/icon-sound.png'

const props = defineProps<{
  bus: CommandBus
  activePanel: 'light' | 'audio' | null
}>()

const emit = defineEmits<{
  toggle: [panel: 'light' | 'audio']
}>()

const isLight = computed(() => props.activePanel === 'light')
const isAudio = computed(() => props.activePanel === 'audio')
</script>

<template>
  <div data-cp-popover="buttons" class="floating-actions absolute right-5 top-[46%] -translate-y-1/2 z-30
              flex flex-col items-center gap-2 select-none">

    <!-- 灯光 -->
    <button
      :aria-pressed="isLight"
      aria-label="打开灯光系统"
      title="灯光系统"
      @click="emit('toggle', 'light')"
      class="fab-img-btn"
    >
      <img
        :src="iconLightUrl"
        alt=""
        aria-hidden="true"
        draggable="false"
        class="fab-img"
        :class="{ 'fab-img--glow': isLight }"
      />
      <span class="fab-label" :class="{ 'fab-label--on': isLight }">灯光</span>
    </button>

    <!-- 音频 -->
    <button
      :aria-pressed="isAudio"
      aria-label="打开音频系统"
      title="音响系统"
      @click="emit('toggle', 'audio')"
      class="fab-img-btn"
    >
      <img
        :src="iconSoundUrl"
        alt=""
        aria-hidden="true"
        draggable="false"
        class="fab-img"
        :class="{ 'fab-img--glow': isAudio }"
      />
      <span class="fab-label" :class="{ 'fab-label--on': isAudio }">音频</span>
    </button>
  </div>
</template>

<style scoped>
.fab-img-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.fab-img-btn:active {
  transform: scale(0.93);
}

/* 默认图片样式 */
.fab-img {
  width: 3.2rem;
  height: 3.2rem;
  object-fit: contain;
  pointer-events: none;
  user-select: none;
  transition: filter 0.3s ease;
}

/* 高亮: 对图片施加 cyan 色调 drop-shadow + 提亮 */
.fab-img--glow {
  filter: brightness(1.4)
          drop-shadow(0 0 6px rgba(52, 224, 255, 0.7))
          drop-shadow(0 0 14px rgba(52, 224, 255, 0.35));
}

/* 文字标签 */
.fab-label {
  font-family: 'Orbitron', 'Rajdhani', sans-serif;
  font-size: 10px;
  letter-spacing: 0.15em;
  color: rgba(255, 255, 255, 0.45);
  transition: color 0.3s ease, text-shadow 0.3s ease;
}

.fab-label--on {
  color: rgba(52, 224, 255, 0.9);
  text-shadow: 0 0 6px rgba(52, 224, 255, 0.4);
}
</style>
