<script setup lang="ts">
/**
 * AudioPanel — 音频控制面板
 *
 * 功能:
 *   - 音量滑块 (0-100)
 *   - TTS 输入框 (调试用)
 *   - 关闭按钮
 */

import { ref, onMounted } from 'vue'

const emit = defineEmits<{
  close: []
  volume: [level: number]
  tts: [text: string]
}>()

const props = defineProps<{
  currentVolume: number
}>()

const volume = ref(props.currentVolume)
const ttsText = ref('')

function onVolumeChange() {
  emit('volume', volume.value)
}

function onTtsSend() {
  const text = ttsText.value.trim()
  if (!text) return
  emit('tts', text)
  ttsText.value = ''
}
</script>

<template>
  <div class="audio-panel">
    <div class="panel-header">
      <span class="panel-title">🔊 音频</span>
      <button class="close-btn" @click="emit('close')" title="关闭">✕</button>
    </div>

    <!-- 音量 -->
    <div class="panel-section">
      <label class="section-label">音量 {{ volume }}%</label>
      <input
        type="range"
        min="0"
        max="100"
        step="5"
        v-model.number="volume"
        @change="onVolumeChange"
        class="volume-slider"
      />
    </div>

    <!-- TTS -->
    <div class="panel-section">
      <label class="section-label">TTS 语音</label>
      <div class="tts-row">
        <input
          type="text"
          v-model="ttsText"
          placeholder="输入文字..."
          class="tts-input"
          @keydown.enter="onTtsSend"
        />
        <button class="tts-btn" @click="onTtsSend" :disabled="!ttsText.trim()">
          播放
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.audio-panel {
  position: absolute;
  right: 76px;
  bottom: 16px;
  width: 220px;
  background: rgba(20, 22, 30, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 12px;
  z-index: 30;
  backdrop-filter: blur(8px);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #e8e6e1;
}

.close-btn {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  border: none;
  color: #8a8d95;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.close-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #e8e6e1;
}

.panel-section {
  margin-bottom: 10px;
}
.panel-section:last-child {
  margin-bottom: 0;
}

.section-label {
  display: block;
  font-size: 11px;
  color: #8a8d95;
  margin-bottom: 6px;
}

/* 音量滑块 */
.volume-slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  outline: none;
}
.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #e8842c;
  cursor: pointer;
  border: 2px solid rgba(0, 0, 0, 0.3);
}
.volume-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #e8842c;
  cursor: pointer;
  border: 2px solid rgba(0, 0, 0, 0.3);
}

/* TTS */
.tts-row {
  display: flex;
  gap: 6px;
}

.tts-input {
  flex: 1;
  height: 30px;
  padding: 0 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  color: #e8e6e1;
  font-size: 12px;
  outline: none;
}
.tts-input::placeholder {
  color: #555860;
}
.tts-input:focus {
  border-color: rgba(232, 132, 44, 0.5);
}

.tts-btn {
  height: 30px;
  padding: 0 10px;
  background: rgba(232, 132, 44, 0.2);
  border: 1px solid rgba(232, 132, 44, 0.4);
  border-radius: 6px;
  color: #e8842c;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.tts-btn:hover:not(:disabled) {
  background: rgba(232, 132, 44, 0.3);
}
.tts-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
