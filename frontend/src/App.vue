<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useWebSocket } from './composables/useWebSocket'
import { useCarStore } from './stores/carStore'
import TopBar from './components/TopBar.vue'
import CameraView from './components/CameraView.vue'
import MotionControl from './components/MotionControl.vue'
import FuncButtons from './components/FuncButtons.vue'
import AudioPanel from './components/AudioPanel.vue'

const ws = useWebSocket()
const store = useCarStore()
const motionControl = ref<any>(null)
const isFullscreen = ref(false)
const showAudioPanel = ref(false)
const audioVolume = ref(80)

onMounted(() => {
  // 订阅遥测
  ws.on('tel.motion', (payload) => store.updateMotion(payload))
  ws.on('tel.sensors', (payload) => store.updateSensors(payload))
  ws.on('event.mode_changed', (payload) => {
    store.mode = payload.mode
  })

  // 延迟测量: 发 ping, 收 pong 算 RTT
  let pingSentAt = 0
  ws.on('event.pong', () => {
    if (pingSentAt > 0) {
      store.wsLatency = Math.round(performance.now() - pingSentAt)
      pingSentAt = 0
    }
  })
  setInterval(() => {
    if (ws.connected.value) {
      pingSentAt = performance.now()
      ws.send('cmd.ping', {})
    }
  }, 2000)

  // 监听全屏变化
  document.addEventListener('fullscreenchange', onFullscreenChange)

  // 同步连接状态
  const check = () => { store.connected = ws.connected.value }
  setInterval(check, 200)

  // 连接
  ws.connect()
})

function sendMotion(vx: number, vy: number) {
  ws.send('cmd.motion', { vx, vy })
}

function sendBrake() {
  motionControl.value?.resetControls()
  ws.send('cmd.brake', {})
}

function sendHorn() {
  ws.send('cmd.audio', { action: 'play', data: { clip: 'horn' } })
}

function sendVolume(level: number) {
  audioVolume.value = level
  ws.send('cmd.audio', { action: 'volume', data: { level } })
}

function sendTts(text: string) {
  ws.send('cmd.audio', { action: 'tts', data: { text } })
}

function toggleAudioPanel() {
  showAudioPanel.value = !showAudioPanel.value
}

async function toggleFullscreen() {
  if (!document.fullscreenElement) {
    try {
      await document.documentElement.requestFullscreen()
      // 全屏后尝试锁定横屏
      try {
        const orientation = screen.orientation as any
        if (orientation?.lock) {
          await orientation.lock('landscape')
        }
      } catch { /* 部分浏览器不支持 */ }
    } catch { /* 全屏请求被拒绝 */ }
  } else {
    await document.exitFullscreen()
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}
</script>

<template>
  <div class="app">
    <TopBar :is-fullscreen="isFullscreen" @toggle-fullscreen="toggleFullscreen" />
    <div class="main-area">
      <CameraView />
      <MotionControl ref="motionControl" @move="sendMotion" />
      <FuncButtons @brake="sendBrake" @horn="sendHorn" @toggle-audio-panel="toggleAudioPanel" />
      <AudioPanel
        v-if="showAudioPanel"
        :current-volume="audioVolume"
        @close="showAudioPanel = false"
        @volume="sendVolume"
        @tts="sendTts"
      />
    </div>
  </div>
</template>

<style>
/* 全局重置 */
* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, #app {
  width: 100%; height: 100%;
  overflow: hidden;
  background: #0d0f14;
  color: #e8e6e1;
  font-family: 'Exo 2', system-ui, sans-serif;
  user-select: none;
  -webkit-user-select: none;
  touch-action: none;
}

.app {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
}

.main-area {
  flex: 1; position: relative; overflow: hidden;
}
</style>
