<!--
  CyberpunkPanel — 新赛博朋克控制面板顶层视图

  布局对照提示词:
    - HUDBar        顶部: 左电量 / 中模式 / 右 连接+信号+延迟+CPU
    - FPVStage      中央主画面 + 左上 FPS/分辨率叠加
    - ReversePiP    左上小窗倒车画中画
    - MoveJoystick  左下 移动虚拟摇杆
    - 右下横排:     云台双轴摇杆 (常驻) + BRAKE + HORN
    - FloatingActionGroup  右侧中部 2 个竖排圆按钮 (灯光/音响)
    - LightPopover / AudioPopover  右侧弹框 (互斥, 外部点击关闭)
    - DataBar       底部中央: 速度 / 里程 / 云台角度
    - 全屏按钮      右上角 (HUD 下方)
-->

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useWebSocket } from '../composables/useWebSocket'
import { useCarStore } from '../stores/carStore'

import HUDBar from './components/HUDBar.vue'
import FPVStage from './components/FPVStage.vue'
import ReversePiP from './components/ReversePiP.vue'
import MoveJoystick from './components/MoveJoystick.vue'
import MiniGimbalStick from './components/MiniGimbalStick.vue'
import BrakeButton from './components/BrakeButton.vue'
import HornButton from './components/HornButton.vue'
import FloatingActionGroup from './components/FloatingActionGroup.vue'
import LightPopover from './components/LightPopover.vue'
import AudioPopover from './components/AudioPopover.vue'
import DataBar from './components/DataBar.vue'
import PanelFrame from './components/PanelFrame.vue'
import bottomRightBgUrl from '../assets/cyberpunk/bottom-right-bg.png'

import { useCommandBus } from './composables/useCommandBus'
import { useStreamFps } from './composables/useStreamFps'

const ws = useWebSocket()
const store = useCarStore()
const bus = useCommandBus(ws)
const { fps, resolution } = useStreamFps()

// ---- 弹框状态 (互斥) ----
const activePanel = ref<'light' | 'audio' | null>(null)

function togglePopover(p: 'light' | 'audio') {
  activePanel.value = activePanel.value === p ? null : p
}

function onRootPointerDown(e: PointerEvent) {
  if (activePanel.value === null) return
  const target = e.target as HTMLElement | null
  if (!target?.closest('[data-cp-popover]')) {
    activePanel.value = null
  }
}

// ---- 全屏（横屏模式） ----
const isFullscreen = ref(!!document.fullscreenElement)

async function toggleFullscreen() {
  if (!document.fullscreenElement) {
    try {
      await document.documentElement.requestFullscreen()
      // 进入全屏后锁定横屏方向
      try {
        await (screen.orientation as any).lock('landscape')
      } catch { /* 部分浏览器/桌面端不支持 orientation lock */ }
    } catch { /* 全屏请求被拒绝 */ }
  } else {
    // 退出全屏时解锁方向
    try {
      (screen.orientation as any).unlock()
    } catch { /* ignore */ }
    await document.exitFullscreen()
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
  // 退出全屏时也解锁方向（用户可能通过手势/系统按钮退出）
  if (!document.fullscreenElement) {
    try {
      (screen.orientation as any).unlock()
    } catch { /* ignore */ }
  }
}

// ---- WebSocket 生命周期 ----
const moveJoyRef = ref<InstanceType<typeof MoveJoystick> | null>(null)
const audioVolume = ref(loadStoredVolume())
const AUDIO_VOLUME_STORAGE_KEY = 'xiaocheng.audioVolume'

function loadStoredVolume(): number {
  try {
    const raw = localStorage.getItem(AUDIO_VOLUME_STORAGE_KEY)
    if (raw === null) return 80
    const n = Number(raw)
    return Number.isFinite(n) ? Math.max(0, Math.min(100, Math.round(n))) : 80
  } catch {
    return 80
  }
}

function saveStoredVolume(level: number) {
  try {
    localStorage.setItem(AUDIO_VOLUME_STORAGE_KEY, String(level))
  } catch { /* ignore */ }
}

onMounted(() => {
  document.addEventListener('fullscreenchange', onFullscreenChange)

  ws.on('tel.motion', (payload) => store.updateMotion(payload))
  ws.on('tel.sensors', (payload) => store.updateSensors(payload))
  ws.on('event.mode_changed', (payload) => {
    if (payload?.mode) store.mode = payload.mode
  })

  ws.on('event.ack', (payload) => {
    if (!payload) return
    if (payload.headlight_on !== undefined || payload.strip_mode !== undefined) {
      store.updateLighting(payload)
    }
    if (payload.nitro !== undefined || payload.active !== undefined) {
      store.updateNitro(payload)
    }
    if (payload.mode) {
      store.mode = payload.mode
    }
  })

  let pingSentAt = 0
  ws.on('event.pong', () => {
    if (pingSentAt > 0) {
      store.wsLatency = Math.round(performance.now() - pingSentAt)
      pingSentAt = 0
    }
  })
  const pingTimer = window.setInterval(() => {
    if (ws.connected.value) {
      pingSentAt = performance.now()
      bus.sendPing()
    }
  }, 2000)

  let volumeSynced = false
  const stateTimer = window.setInterval(() => {
    store.connected = ws.connected.value
    if (!ws.connected.value) {
      volumeSynced = false
      return
    }
    if (!volumeSynced) {
      volumeSynced = true
      bus.sendVolume(audioVolume.value)
    }
  }, 200)

  ws.connect()

  onUnmounted(() => {
    window.clearInterval(pingTimer)
    window.clearInterval(stateTimer)
    document.removeEventListener('fullscreenchange', onFullscreenChange)
  })
})

function onBrakePress() {
  moveJoyRef.value?.reset()
}

function onVolumeChange(v: number) {
  audioVolume.value = v
  saveStoredVolume(v)
}
</script>

<template>
  <div
    class="relative w-full h-full overflow-hidden bg-hull-900"
    @pointerdown="onRootPointerDown"
  >
    <!-- 主画面: FPS/分辨率叠加在画面左上角 -->
    <FPVStage :fps="fps" :resolution="resolution" />
    <PanelFrame />

    <!-- 顶部 HUD -->
    <HUDBar :bus="bus" />

    <!-- 倒车 PiP (左上), fps/分辨率显示在 PiP 上方 -->
    <ReversePiP :fps="fps" :resolution="resolution" />

    <!-- 左下: 移动摇杆 -->
    <MoveJoystick ref="moveJoyRef" :bus="bus" />

    <!-- 右下横排: 云台小摇杆 + BRAKE + HORN，底图铺满 -->
    <div class="absolute bottom-4 right-3 z-20 flex items-center gap-2 select-none"
         style="padding: 10px 14px;">
      <!-- 背景底图 -->
      <img
        :src="bottomRightBgUrl"
        alt=""
        aria-hidden="true"
        draggable="false"
        class="absolute inset-0 w-full h-full object-fill pointer-events-none select-none"
      />
      <MiniGimbalStick :bus="bus" />
      <BrakeButton :bus="bus" @press="onBrakePress" />
      <HornButton :bus="bus" />
    </div>

    <!-- 右侧中部: 2 个竖排浮动圆按钮 (灯光 / 音响) -->
    <FloatingActionGroup
      :bus="bus"
      :active-panel="activePanel"
      @toggle="togglePopover"
    />

    <!-- 弹框 (互斥): Teleport 到 body 避免受父级 relative 影响 -->
    <Teleport to="body">
      <div
        v-if="activePanel"
        data-cp-popover="overlay"
        class="fixed inset-0 z-[9999] pointer-events-none"
      >
        <LightPopover v-if="activePanel === 'light'" :bus="bus" />
        <AudioPopover
          v-if="activePanel === 'audio'"
          :bus="bus"
          :initial-volume="audioVolume"
          @volume-change="onVolumeChange"
        />
      </div>
    </Teleport>

    <!-- 底部数据条 (居中) -->
    <DataBar />

    <!-- 全屏按钮 (右上角, 避开 HUD) -->
    <button
      class="fullscreen-btn absolute top-14 right-4 z-30"
      :title="isFullscreen ? '退出全屏' : '全屏'"
      @click="toggleFullscreen"
    >
      <!-- 进入全屏图标 -->
      <svg v-if="!isFullscreen" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M3 3h6v2H5v4H3V3z"/>
        <path d="M21 3h-6v2h4v4h2V3z"/>
        <path d="M3 21h6v-2H5v-4H3v6z"/>
        <path d="M21 21h-6v-2h4v-4h2v6z"/>
      </svg>
      <!-- 退出全屏图标 -->
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M9 3v6H3v-2h4V3h2z"/>
        <path d="M15 3v4h4v2h-6V3h2z"/>
        <path d="M9 21v-6H3v2h4v4h2z"/>
        <path d="M15 21v-4h4v-2h-6v6h2z"/>
      </svg>
    </button>
  </div>
</template>

<style scoped>
.fullscreen-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid rgba(52, 224, 255, 0.35);
  background: rgba(5, 7, 12, 0.7);
  color: rgba(52, 224, 255, 0.85);
  backdrop-filter: blur(4px);
  transition: all 0.2s ease;
  cursor: pointer;
}
.fullscreen-btn:hover {
  background: rgba(52, 224, 255, 0.15);
  border-color: rgba(52, 224, 255, 0.6);
  box-shadow: 0 0 12px rgba(52, 224, 255, 0.3);
  color: #34e0ff;
}
.fullscreen-btn:active {
  transform: scale(0.92);
}
</style>
