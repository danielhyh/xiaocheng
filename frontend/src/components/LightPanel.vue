<script setup lang="ts">
/**
 * LightPanel — 灯光控制面板
 *
 * 前大灯开关 + 亮度滑块
 * 灯带模式选择 (尾灯/警灯/氛围灯)
 */

import { ref, watch } from 'vue'
import { useCarStore } from '../stores/carStore'

const store = useCarStore()

const emit = defineEmits<{
  close: []
  headlight: [data: { on?: boolean; brightness?: number }]
  stripMode: [mode: string]
}>()

const headlightOn = ref(store.lighting.headlight_on)
const headlightBrightness = ref(store.lighting.headlight_brightness)

// 同步 store 变化
watch(() => store.lighting.headlight_on, (v) => { headlightOn.value = v })
watch(() => store.lighting.headlight_brightness, (v) => { headlightBrightness.value = v })

const stripModes = [
  { id: 'off',     label: '关闭',   icon: '○' },
  { id: 'tail',    label: '尾灯',   icon: '◉' },
  { id: 'police',  label: '警灯',   icon: '🚨' },
  { id: 'ambient', label: '氛围',   icon: '🌈' },
]

function toggleHeadlight() {
  headlightOn.value = !headlightOn.value
  emit('headlight', { on: headlightOn.value })
}

function onBrightnessChange(e: Event) {
  const val = Number((e.target as HTMLInputElement).value)
  headlightBrightness.value = val
  emit('headlight', { brightness: val })
}

function selectStripMode(mode: string) {
  emit('stripMode', mode)
}
</script>

<template>
  <div class="light-panel" @click.stop>
    <!-- 关闭按钮 -->
    <button class="close-btn" @click="emit('close')" title="关闭">✕</button>

    <div class="panel-title">灯光控制</div>

    <!-- 前大灯 -->
    <div class="section">
      <div class="section-label">前大灯</div>
      <div class="headlight-row">
        <button
          class="headlight-toggle"
          :class="{ active: headlightOn }"
          @click="toggleHeadlight"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2a7 7 0 0 1 4 12.7V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.3A7 7 0 0 1 12 2z"/>
            <line x1="9" y1="21" x2="15" y2="21"/>
          </svg>
          <span>{{ headlightOn ? 'ON' : 'OFF' }}</span>
        </button>
        <div class="brightness-slider" :class="{ disabled: !headlightOn }">
          <input
            type="range"
            min="10"
            max="100"
            :value="headlightBrightness"
            :disabled="!headlightOn"
            @input="onBrightnessChange"
          />
          <span class="brightness-val">{{ headlightBrightness }}%</span>
        </div>
      </div>
    </div>

    <!-- 灯带模式 -->
    <div class="section">
      <div class="section-label">灯带模式</div>
      <div class="mode-grid">
        <button
          v-for="m in stripModes"
          :key="m.id"
          class="mode-btn"
          :class="{ active: store.lighting.strip_mode === m.id }"
          @click="selectStripMode(m.id)"
        >
          <span class="mode-icon">{{ m.icon }}</span>
          <span class="mode-label">{{ m.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.light-panel {
  position: absolute;
  right: 72px;
  top: 50%;
  transform: translateY(-50%);
  width: 220px;
  background: rgba(20, 22, 30, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  padding: 14px;
  z-index: 30;
  backdrop-filter: blur(12px);
}

.close-btn {
  position: absolute;
  top: 8px;
  right: 10px;
  background: none;
  border: none;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  padding: 2px 6px;
}
.close-btn:hover { color: #aaa; }

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #e8e6e1;
  margin-bottom: 12px;
}

.section {
  margin-bottom: 14px;
}
.section:last-child { margin-bottom: 0; }

.section-label {
  font-size: 11px;
  color: #8a8d95;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 前大灯 */
.headlight-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.headlight-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(30, 34, 43, 0.8);
  color: #8a8d95;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.headlight-toggle svg {
  width: 16px;
  height: 16px;
  stroke: #8a8d95;
  fill: none;
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: all 0.2s;
}
.headlight-toggle.active {
  background: rgba(255, 200, 50, 0.2);
  border-color: rgba(255, 200, 50, 0.5);
  color: #ffc832;
}
.headlight-toggle.active svg {
  stroke: #ffc832;
  fill: rgba(255, 200, 50, 0.3);
}

.brightness-slider {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}
.brightness-slider.disabled { opacity: 0.4; }

.brightness-slider input[type="range"] {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  outline: none;
}
.brightness-slider input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #ffc832;
  cursor: pointer;
}

.brightness-val {
  font-size: 11px;
  color: #8a8d95;
  min-width: 32px;
  text-align: right;
}

/* 灯带模式 */
.mode-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 4px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(30, 34, 43, 0.7);
  color: #8a8d95;
  cursor: pointer;
  transition: all 0.2s;
}
.mode-btn:hover {
  background: rgba(40, 44, 53, 0.8);
}
.mode-btn.active {
  background: rgba(88, 166, 255, 0.15);
  border-color: rgba(88, 166, 255, 0.4);
  color: #58a6ff;
}

.mode-icon { font-size: 16px; }
.mode-label { font-size: 10px; }
</style>
