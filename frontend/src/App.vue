<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useWebSocket } from './composables/useWebSocket'
import { useCarStore } from './stores/carStore'
import TopBar from './components/TopBar.vue'
import CameraView from './components/CameraView.vue'
import MotionControl from './components/MotionControl.vue'
import FuncButtons from './components/FuncButtons.vue'

const ws = useWebSocket()
const store = useCarStore()
const motionControl = ref<any>(null)

onMounted(() => {
  // 订阅遥测
  ws.on('tel.motion', (payload) => store.updateMotion(payload))
  ws.on('tel.sensors', (payload) => store.updateSensors(payload))
  ws.on('event.mode_changed', (payload) => {
    store.mode = payload.mode
  })

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
</script>

<template>
  <div class="app">
    <TopBar />
    <div class="main-area">
      <CameraView />
      <MotionControl ref="motionControl" @move="sendMotion" />
      <FuncButtons @brake="sendBrake" />
    </div>
  </div>
</template>

<style>
/* 全局重置 + 横屏布局 */
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
