<!--
  AudioPopover — 音响弹框 (R11)

  音量 / 麦克风 / TTS
  Teleport 到 body 后用 fixed 定位
-->

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { CommandBus } from '../composables/useCommandBus'

const props = defineProps<{
  bus: CommandBus
  initialVolume: number
}>()

const emit = defineEmits<{
  volumeChange: [level: number]
}>()

const volume = ref(clampVolume(props.initialVolume))
const micOn = ref(false)
const ttsOn = ref(true)
const ttsText = ref('')

watch(() => props.initialVolume, (v) => { volume.value = clampVolume(v) })

function clampVolume(v: number) {
  return Math.max(0, Math.min(100, Math.round(v)))
}

function onVolumeInput(e: Event) {
  const v = clampVolume(Number((e.target as HTMLInputElement).value))
  volume.value = v
  props.bus.sendVolume(v)
  emit('volumeChange', v)
}

function toggleMic() {
  micOn.value = !micOn.value
}

function submitTts() {
  const text = ttsText.value.trim()
  if (!text || !ttsOn.value) return
  props.bus.sendTts(text)
  ttsText.value = ''
}
</script>

<template>
  <div
    data-cp-popover="audio"
    class="cp-popover pointer-events-auto"
    style="position: fixed; right: 84px; top: 50%; transform: translateY(-50%);"
    @pointerdown.stop
    @click.stop
  >
    <!-- 切角装饰 -->
    <span class="corner corner-tl"></span>
    <span class="corner corner-tr"></span>
    <span class="corner corner-bl"></span>
    <span class="corner corner-br"></span>

    <div class="cp-scanline"></div>

    <!-- 标题栏 -->
    <div class="popover-header">
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5 text-neon-cyan" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 5L6 9H2v6h4l5 4V5z"/>
          <path d="M15.5 8.5a5 5 0 0 1 0 7"/>
          <path d="M19 5a9 9 0 0 1 0 14"/>
        </svg>
        <span class="popover-title">音频系统</span>
      </div>
    </div>

    <div class="popover-body">
      <!-- 音量 -->
      <div class="row">
        <span class="row-label">音量</span>
        <svg class="w-4 h-4 text-white/70 shrink-0" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 5L6 9H2v6h4l5 4V5z"/>
          <line x1="22" y1="9" x2="16" y2="15"/>
          <line x1="16" y1="9" x2="22" y2="15"/>
        </svg>
        <input
          type="range" min="0" max="100" step="1"
          aria-label="音量"
          :value="volume"
          @input="onVolumeInput"
          class="cp-range flex-1"
        />
        <span class="cp-mono text-neon-cyan text-[13px] w-10 text-right">{{ volume }}%</span>
      </div>

      <!-- 麦克风 -->
      <div class="row justify-between">
        <span class="row-label">麦克风</span>
        <button class="cp-switch" role="switch" aria-label="麦克风开关" :aria-checked="micOn" @click="toggleMic"></button>
      </div>

      <!-- TTS 开关 -->
      <div class="row justify-between">
        <span class="row-label whitespace-nowrap">语音播报 (TTS)</span>
        <button class="cp-switch" role="switch" aria-label="语音播报开关" :aria-checked="ttsOn"
                @click="ttsOn = !ttsOn"></button>
      </div>

      <!-- TTS 输入 -->
      <div class="tts-input-wrap" :class="{ 'is-disabled': !ttsOn }">
        <input
          v-model="ttsText"
          :disabled="!ttsOn"
          type="text"
          aria-label="语音播报文字"
          placeholder="TTS: 请输入文字..."
          class="tts-input"
          @keydown.enter="submitTts"
        />
        <button
          class="tts-send"
          :disabled="!ttsOn || !ttsText.trim()"
          @click="submitTts"
          title="播放"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 20h9"/>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cp-popover {
  width: 280px;
  padding: 14px 16px 16px;
  z-index: 10000;
  background: linear-gradient(180deg, rgba(8, 18, 32, 0.92), rgba(6, 12, 22, 0.92));
  border: 1px solid rgba(52, 224, 255, 0.55);
  border-radius: 6px;
  backdrop-filter: blur(14px) saturate(140%);
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  box-shadow:
    0 0 0 1px rgba(52, 224, 255, 0.08) inset,
    0 0 22px rgba(52, 224, 255, 0.18),
    0 8px 30px rgba(0, 0, 0, 0.6);
}

/* L 形角标 */
.corner {
  position: absolute;
  width: 14px;
  height: 14px;
  pointer-events: none;
}
.corner-tl { top: -1px; left: -1px; border-top: 2px solid #34e0ff; border-left: 2px solid #34e0ff; border-top-left-radius: 6px; }
.corner-tr { top: -1px; right: -1px; border-top: 2px solid #34e0ff; border-right: 2px solid #34e0ff; border-top-right-radius: 6px; }
.corner-bl { bottom: -1px; left: -1px; border-bottom: 2px solid #34e0ff; border-left: 2px solid #34e0ff; border-bottom-left-radius: 6px; }
.corner-br { bottom: -1px; right: -1px; border-bottom: 2px solid #34e0ff; border-right: 2px solid #34e0ff; border-bottom-right-radius: 6px; }

.popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 10px;
  margin-bottom: 12px;
  border-bottom: 1px solid rgba(52, 224, 255, 0.2);
}

.popover-title {
  font-family: var(--font-display);
  font-size: 15px;
  letter-spacing: 0.18em;
  color: #aef0ff;
  text-shadow: 0 0 6px rgba(52, 224, 255, 0.35);
}

.popover-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.row-label {
  font-family: var(--font-display);
  font-size: 13px;
  color: rgba(230, 245, 255, 0.85);
  letter-spacing: 0.05em;
  min-width: 38px;
}

/* TTS 输入框 */
.tts-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  height: 34px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(52, 224, 255, 0.35);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.tts-input-wrap:focus-within {
  border-color: rgba(52, 224, 255, 0.8);
  box-shadow: 0 0 10px rgba(52, 224, 255, 0.35);
}

.tts-input-wrap.is-disabled {
  opacity: 0.5;
}

.tts-input {
  flex: 1;
  height: 100%;
  background: transparent;
  border: none;
  outline: none;
  padding: 0 10px;
  color: rgba(230, 245, 255, 0.95);
  font-family: var(--font-display);
  font-size: 13px;
  letter-spacing: 0.04em;
}

.tts-input::placeholder {
  color: rgba(180, 210, 230, 0.45);
}

.tts-send {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 100%;
  background: transparent;
  border: none;
  border-left: 1px solid rgba(52, 224, 255, 0.25);
  color: #34e0ff;
  cursor: pointer;
  transition: background 0.18s ease;
}

.tts-send:hover:not(:disabled) {
  background: rgba(52, 224, 255, 0.12);
}

.tts-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

</style>
