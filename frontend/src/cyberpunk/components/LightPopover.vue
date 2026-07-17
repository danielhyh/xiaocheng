<!--
  LightPopover — 灯光弹框 (R10)

  大灯开关 + 亮度 (0–100) + 灯带模式选择
  Teleport 到 body 后用 fixed 定位, 内联 position 覆盖 .cp-panel 的 relative
  外部点击关闭由父级 CyberpunkPanel.onRootPointerDown 处理
-->

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useCarStore } from '../../stores/carStore'
import type { CommandBus } from '../composables/useCommandBus'

const props = defineProps<{ bus: CommandBus }>()

const store = useCarStore()

const headlightOn = ref(store.lighting.headlight_on)
const brightness = ref(store.lighting.headlight_brightness)

watch(() => store.lighting.headlight_on, (v) => { headlightOn.value = v })
watch(() => store.lighting.headlight_brightness, (v) => { brightness.value = v })

// 6 档常用模式 (与图示一致)
// key 用于前端高亮去重 (后端无法区分 呼吸/氛围灯, 都映射到 ambient)
const stripModes = [
  { key: 'off',      label: '关闭',   sendId: 'off' },
  { key: 'tail',     label: '常亮',   sendId: 'tail' },
  { key: 'breath',   label: '呼吸',   sendId: 'ambient' },
  { key: 'reverse',  label: '流水',   sendId: 'reverse' },
  { key: 'police',   label: '警灯',   sendId: 'police' },
  { key: 'ambient',  label: '氛围灯', sendId: 'ambient' },
]

// 本地激活态: 跟随用户点击, 后端 ack 同步时如能匹配就同步
const activeKey = ref<string>('off')

watch(() => store.lighting.strip_mode, (mode) => {
  // 后端模式变化时, 仅当当前选中项的 sendId 与新模式不一致才同步
  const current = stripModes.find((m) => m.key === activeKey.value)
  if (!current || current.sendId !== mode) {
    const match = stripModes.find((m) => m.sendId === mode)
    if (match) activeKey.value = match.key
  }
}, { immediate: true })

function toggleHeadlight() {
  headlightOn.value = !headlightOn.value
  props.bus.sendHeadlight({ on: headlightOn.value })
}

function onBrightness(e: Event) {
  const v = Number((e.target as HTMLInputElement).value)
  brightness.value = v
  props.bus.sendHeadlight({ brightness: v })
}

function selectMode(mode: { key: string; sendId: string }) {
  activeKey.value = mode.key
  props.bus.sendStripMode(mode.sendId)
}
</script>

<template>
  <div
    data-cp-popover="light"
    class="cp-popover pointer-events-auto"
    style="position: fixed; right: 84px; top: 50%; transform: translateY(-50%);"
    @pointerdown.stop
    @click.stop
  >
    <!-- 切角装饰: 4 个 L 形角标 -->
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
          <path d="M9 21h6"/>
          <path d="M12 3a6 6 0 0 1 4 10.4V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-3.6A6 6 0 0 1 12 3z"/>
          <path d="M12 7v0"/>
        </svg>
        <span class="popover-title">灯光系统</span>
      </div>
    </div>

    <div class="popover-body">
      <!-- 前大灯开关 -->
      <div class="row">
        <span class="row-label">前大灯</span>
        <button
          class="cp-switch"
          role="switch"
          :aria-checked="headlightOn"
          @click="toggleHeadlight"
        ></button>
      </div>

      <!-- 亮度 -->
      <div class="row">
        <span class="row-label">亮度</span>
        <input
          type="range" min="10" max="100"
          :value="brightness" :disabled="!headlightOn"
          @input="onBrightness"
          class="cp-range flex-1"
          :class="{ 'opacity-40': !headlightOn }"
        />
        <span class="cp-mono text-neon-cyan text-[13px] w-10 text-right">{{ brightness }}%</span>
      </div>

      <!-- 模式 -->
      <div class="mt-1">
        <div class="row-label mb-2">模式</div>
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="m in stripModes"
            :key="m.key"
            class="mode-btn"
            :class="{ 'mode-btn--on': activeKey === m.key }"
            @click="selectMode(m)"
          >
            {{ m.label }}
          </button>
        </div>
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

/* 模式按钮 */
.mode-btn {
  height: 36px;
  border-radius: 6px;
  font-family: var(--font-display);
  font-size: 13px;
  letter-spacing: 0.08em;
  background: rgba(10, 22, 38, 0.6);
  border: 1px solid rgba(52, 224, 255, 0.4);
  color: rgba(200, 230, 245, 0.85);
  cursor: pointer;
  transition: all 0.18s ease;
}

.mode-btn:hover {
  border-color: rgba(52, 224, 255, 0.7);
  background: rgba(52, 224, 255, 0.08);
  color: #eafcff;
}

.mode-btn:active {
  transform: translateY(1px);
}

.mode-btn--on {
  background: linear-gradient(180deg, rgba(52, 224, 255, 0.28), rgba(52, 224, 255, 0.08));
  border-color: #34e0ff;
  color: #eafcff;
  box-shadow:
    0 0 0 1px rgba(52, 224, 255, 0.6) inset,
    0 0 14px rgba(52, 224, 255, 0.55),
    0 0 28px rgba(52, 224, 255, 0.25);
  text-shadow: 0 0 6px rgba(52, 224, 255, 0.6);
}
</style>
