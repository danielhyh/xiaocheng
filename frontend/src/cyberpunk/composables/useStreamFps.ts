/**
 * useStreamFps — 周期性拉取 /stream/status 显示 FPS / 分辨率
 */

import { onMounted, onUnmounted, ref } from 'vue'

export function useStreamFps(intervalMs = 2000) {
  const fps = ref<number | null>(null)
  const resolution = ref<string | null>(null)
  let timer: number | null = null

  async function fetchOnce() {
    try {
      const base = `${location.protocol}//${location.hostname}:${location.port || 8000}`
      const res = await fetch(`${base}/stream/status`)
      if (!res.ok) return
      const data = await res.json()
      fps.value = typeof data.fps === 'number' ? data.fps : null
      if (Array.isArray(data.resolution) && data.resolution.length === 2) {
        resolution.value = `${data.resolution[0]}×${data.resolution[1]}`
      }
    } catch {
      // 后端暂不可用, 保持占位
    }
  }

  onMounted(() => {
    fetchOnce()
    timer = window.setInterval(fetchOnce, intervalMs)
  })

  onUnmounted(() => {
    if (timer !== null) {
      window.clearInterval(timer)
      timer = null
    }
  })

  return { fps, resolution }
}
