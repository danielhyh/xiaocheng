/**
 * useKeepaliveSender — 100 ± 20 ms 保活发送定时器
 *
 * 对应 R6.3 / R7.3 / P7: 在按住摇杆期间以 100ms 周期发送当前向量。
 * 对应 R8.2 / P4: 支持作为 BRAKE 的按住循环发送器复用。
 *
 * 设计:
 *   - start(): 立刻发送首帧, 随后 setInterval(100) 循环
 *   - stop():  清理定时器, 可选发送一次 "stop payload" (如 (0,0))
 *   - setPayload(): 拖动过程中更新将要发送的内容
 *
 * 与 WebSocket 解耦: 只调用注入的 emit 函数, 便于测试与 PBT。
 */

import { onBeforeUnmount } from 'vue'

export interface KeepaliveOptions<T> {
  /** 每次心跳发送的回调 */
  emit: (payload: T) => void
  /** 心跳周期, 默认 100ms */
  periodMs?: number
}

export function useKeepaliveSender<T>(options: KeepaliveOptions<T>) {
  const period = options.periodMs ?? 100
  let timer: number | null = null
  let payload: T | null = null

  function setPayload(p: T) {
    payload = p
  }

  function start(initial: T) {
    if (timer !== null) {
      // 已在运行: 只更新 payload, 不重启计时器
      payload = initial
      return
    }
    payload = initial
    // 首帧立即发送, 满足 R8.2 "首帧 ≤ 20 ms 内"
    options.emit(payload)
    timer = window.setInterval(() => {
      if (payload !== null) options.emit(payload)
    }, period)
  }

  function stop(finalPayload?: T) {
    if (timer !== null) {
      window.clearInterval(timer)
      timer = null
    }
    if (finalPayload !== undefined) {
      options.emit(finalPayload)
    }
    payload = null
  }

  function isRunning() {
    return timer !== null
  }

  onBeforeUnmount(() => stop())

  return { start, stop, setPayload, isRunning }
}
