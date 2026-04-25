/**
 * useWebSocket — 统一 WS 连接管理
 *
 * 职责:
 *   - 连接 / 自动重连 (指数退避)
 *   - envelope 发送 (自动加 ts)
 *   - 按 type 前缀路由收到的消息
 *   - 暴露连接状态给 UI
 */

import { ref, onUnmounted } from 'vue'

export type MessageHandler = (payload: any, msg: any) => void

interface UseWebSocketOptions {
  url?: string
  reconnect?: boolean
  maxRetries?: number
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    url = `ws://${location.host}/ws/control`,
    reconnect = true,
    maxRetries = 10,
  } = options

  const connected = ref(false)
  const retryCount = ref(0)

  let ws: WebSocket | null = null
  let handlers: Map<string, MessageHandler[]> = new Map()
  let reconnectTimer: number | null = null

  // ---- 连接 ----

  function connect() {
    if (ws?.readyState === WebSocket.OPEN) return

    ws = new WebSocket(url)

    ws.onopen = () => {
      connected.value = true
      retryCount.value = 0
      console.log('[WS] 已连接')
    }

    ws.onclose = () => {
      connected.value = false
      console.log('[WS] 断开')
      if (reconnect && retryCount.value < maxRetries) {
        const delay = Math.min(1000 * 2 ** retryCount.value, 10000)
        console.log(`[WS] ${delay}ms 后重连...`)
        reconnectTimer = window.setTimeout(() => {
          retryCount.value++
          connect()
        }, delay)
      }
    }

    ws.onerror = (e) => {
      console.error('[WS] 错误', e)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        routeMessage(msg)
      } catch (e) {
        console.warn('[WS] 解析失败', event.data)
      }
    }
  }

  // ---- 消息路由 ----

  function routeMessage(msg: any) {
    const type: string = msg.type || ''

    // 精确匹配
    const exact = handlers.get(type)
    if (exact) exact.forEach((h) => h(msg.payload, msg))

    // 前缀匹配: "tel.*" 匹配所有 tel.xxx
    for (const [pattern, fns] of handlers) {
      if (pattern.endsWith('.*')) {
        const prefix = pattern.slice(0, -1)
        if (type.startsWith(prefix)) {
          fns.forEach((h) => h(msg.payload, msg))
        }
      }
    }
  }

  // ---- 订阅 ----

  function on(type: string, handler: MessageHandler) {
    if (!handlers.has(type)) handlers.set(type, [])
    handlers.get(type)!.push(handler)
  }

  // ---- 发送 ----

  function send(type: string, payload: any, id?: string) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return

    const envelope: any = {
      type,
      ts: Date.now() / 1000,
      payload,
    }
    if (id) envelope.id = id

    ws.send(JSON.stringify(envelope))
  }

  // ---- 断开 ----

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws?.close()
    ws = null
    connected.value = false
  }

  // 组件卸载时断开
  onUnmounted(() => disconnect())

  return {
    connected,
    retryCount,
    connect,
    disconnect,
    send,
    on,
  }
}
