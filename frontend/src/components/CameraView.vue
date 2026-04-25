<script setup lang="ts">
// Phase 3: 替换为 <img :src="mjpegUrl" /> MJPEG 流
</script>

<template>
  <div class="camera-view">
    <div class="placeholder">
      <div class="cam-icon">
        <div class="cam-inner"></div>
      </div>
      <span class="label">Camera offline</span>
      <span class="phase">Phase 3</span>
    </div>

    <!-- HUD 叠加层: 十字准星 + 角落框 -->
    <div class="crosshair"></div>
    <div class="bracket tl"></div>
    <div class="bracket tr"></div>
    <div class="bracket bl"></div>
    <div class="bracket br"></div>
  </div>
</template>

<style scoped>
.camera-view {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
}
.placeholder {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  color: #555860; font-size: 13px; font-weight: 500;
}
.cam-icon {
  width: 40px; height: 40px; border: 2px solid #555860;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.cam-inner { width: 16px; height: 16px; border: 2px solid #555860; border-radius: 50%; }
.phase { font-size: 11px; }

.crosshair {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 60px; height: 60px; opacity: 0.15; pointer-events: none;
}
.crosshair::before, .crosshair::after {
  content: ''; position: absolute; background: #e8e6e1;
}
.crosshair::before { width: 1px; height: 100%; left: 50%; }
.crosshair::after  { height: 1px; width: 100%; top: 50%; }

.bracket {
  position: absolute; width: 18px; height: 18px;
  border-color: #e8842c; border-style: solid; border-width: 0;
  opacity: 0.3; pointer-events: none;
}
.bracket.tl { top: 20%; left: 15%; border-top-width: 2px; border-left-width: 2px; }
.bracket.tr { top: 20%; right: 15%; border-top-width: 2px; border-right-width: 2px; }
.bracket.bl { bottom: 20%; left: 15%; border-bottom-width: 2px; border-left-width: 2px; }
.bracket.br { bottom: 20%; right: 15%; border-bottom-width: 2px; border-right-width: 2px; }
</style>
