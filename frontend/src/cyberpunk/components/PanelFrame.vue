<!--
  PanelFrame — 赛博朋克外框装饰层

  - 背景网格 (radial 渐变淡出) 营造氛围
  - 整体边框装饰 PNG (panel-frame-border) 铺满视口, 透明底, 不拦截交互
  - pointer-events: none, 始终盖在 FPV 之上、交互控件之下
-->

<script setup lang="ts">
import frameBorderUrl from '../../assets/cyberpunk/panel-border.png'
</script>

<template>
  <div class="absolute inset-0 pointer-events-none z-[5]">
    <!-- 背景网格 (兜底 + 氛围) -->
    <div class="absolute inset-0 opacity-[0.12]"
         :style="{
           backgroundImage:
             'linear-gradient(rgba(52,224,255,.5) 1px, transparent 1px),' +
             'linear-gradient(90deg, rgba(52,224,255,.4) 1px, transparent 1px)',
           backgroundSize: '60px 60px, 60px 60px',
           maskImage: 'radial-gradient(ellipse at center, black 25%, transparent 78%)',
           WebkitMaskImage: 'radial-gradient(ellipse at center, black 25%, transparent 78%)',
         }">
    </div>

    <!-- 整体边框装饰: 源 PNG 16:9, 铺满视口时边框贴合四边 -->
    <img
      :src="frameBorderUrl"
      alt=""
      aria-hidden="true"
      draggable="false"
      class="absolute inset-0 w-full h-full select-none"
      style="object-fit: fill;"
    />
  </div>
</template>
