/**
 * mockStreamFps — Mock 模式下的 FPS 数据源
 *
 * 不请求 /stream/status, 直接返回模拟值。
 */

import { onMounted, onUnmounted, ref } from 'vue'
import { getMockConfig } from './mockTelemetry'

export function useMockStreamFps() {
  const fps = ref<number | null>(null)
  const resolution = ref<string | null>('1920×1080')
  let timer: number | null = null

  onMounted(() => {
    fps.value = getMockConfig().fps
    timer = window.setInterval(() => {
      const base = getMockConfig().fps
      fps.value = base + Math.round((Math.random() - 0.5) * 2)
    }, 2000)
  })

  onUnmounted(() => {
    if (timer !== null) window.clearInterval(timer)
  })

  return { fps, resolution }
}
