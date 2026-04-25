<script setup lang="ts">
/**
 * FuncButtons — 右侧功能按钮 (占位)
 *
 * 灰掉的按钮标注对应 Phase,
 * 后续 Phase 完成后激活并接入实际功能。
 */

const buttons = [
  { icon: 'gimbal',  label: 'P6',  phase: 6  },
  { icon: 'light',   label: 'P8',  phase: 8  },
  { icon: 'audio',   label: 'P9',  phase: 9  },
  { icon: 'nitro',   label: 'P10', phase: 10 },
]

const emit = defineEmits<{
  brake: []
}>()
</script>

<template>
  <div class="func-col">
    <div class="func-item">
      <button class="fbtn brake" title="刹车" @click="emit('brake')">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="8"/>
          <path d="M12 7v6"/>
          <path d="M12 16h.01"/>
        </svg>
      </button>
      <span class="fbtn-lbl brake-lbl">BRAKE</span>
    </div>
    <div v-for="btn in buttons" :key="btn.icon" class="func-item">
      <button class="fbtn" disabled :title="`Phase ${btn.phase}`">
        <!-- Gimbal -->
        <svg v-if="btn.icon === 'gimbal'" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>
        </svg>
        <!-- Light -->
        <svg v-else-if="btn.icon === 'light'" viewBox="0 0 24 24">
          <path d="M12 2a7 7 0 0 1 4 12.7V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.3A7 7 0 0 1 12 2z"/>
          <line x1="9" y1="21" x2="15" y2="21"/>
        </svg>
        <!-- Audio -->
        <svg v-else-if="btn.icon === 'audio'" viewBox="0 0 24 24">
          <path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/>
        </svg>
        <!-- Nitro -->
        <svg v-else-if="btn.icon === 'nitro'" viewBox="0 0 24 24">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </button>
      <span class="fbtn-lbl">{{ btn.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.func-col {
  position: absolute; right: 16px; top: 44px; bottom: 16px;
  width: 52px; z-index: 20;
  display: flex; flex-direction: column; align-items: center;
  justify-content: flex-end; gap: 8px;
}
.func-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.fbtn {
  width: 44px; height: 44px; border-radius: 12px;
  background: #1e222b; border: 1px solid rgba(255,255,255,0.06);
  display: flex; align-items: center; justify-content: center;
  cursor: not-allowed; opacity: 0.3;
}
.fbtn.brake {
  cursor: pointer; opacity: 1;
  background: #3a1518; border-color: rgba(255, 88, 88, 0.45);
}
.fbtn.brake:hover { background: #48191d; }
.fbtn.brake:active { transform: translateY(1px); }
.fbtn svg {
  width: 20px; height: 20px; stroke: #8a8d95; fill: none;
  stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round;
}
.fbtn.brake svg { stroke: #ff6b6b; }
.fbtn-lbl { font-size: 11px; color: #555860; }
.brake-lbl { color: #ff6b6b; }
</style>
