<script setup lang="ts">
import { useCarStore } from '../stores/carStore'
const store = useCarStore()
</script>

<template>
  <div class="topbar">
    <div class="topbar-left">
      <span class="brand">小橙</span>
      <span class="mode-chip">{{ store.mode }}</span>
      <span class="conn">
        <span class="dot" :class="store.connected ? 'on' : 'off'"></span>
        <span :style="{ color: store.connected ? '#2dd284' : '#e24b4a' }">
          {{ store.connected ? 'connected' : 'offline' }}
        </span>
      </span>
    </div>
    <div class="topbar-right">
      <span class="stat">BAT <b>{{ store.sensors.battery_voltage.toFixed(1) }}V</b></span>
      <span class="stat">CPU <b>{{ Math.round(store.sensors.cpu_temp) }}°C</b></span>
      <span class="stat">PING <b>{{ Math.round(store.sensors.ws_latency_ms) }}ms</b></span>
    </div>
  </div>
</template>

<style scoped>
.topbar {
  height: 36px; padding: 0 16px;
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(13,15,20,0.95);
  font-size: 12px; z-index: 10; flex-shrink: 0;
}
.topbar-left, .topbar-right { display: flex; align-items: center; gap: 12px; }
.brand { font-weight: 700; font-size: 14px; color: #e8842c; letter-spacing: 1px; }
.mode-chip {
  background: rgba(232,132,44,0.15); color: #e8842c;
  padding: 2px 10px; border-radius: 10px; font-size: 11px;
  font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;
}
.conn { display: flex; align-items: center; gap: 4px; font-size: 11px; }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.dot.on { background: #2dd284; }
.dot.off { background: #e24b4a; }
.stat { color: #8a8d95; font-family: 'JetBrains Mono', monospace; font-size: 11px; }
.stat b { color: #e8e6e1; font-weight: 500; }
</style>
