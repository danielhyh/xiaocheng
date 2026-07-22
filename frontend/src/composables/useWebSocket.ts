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
  const wsScheme = location.protocol === 'https:' ? 'wss' : 'ws'
  const {
    url = `${wsScheme}://${location.host}/ws/control`,
    reconnect = true,
    maxRetries = 10,
  } = options

  const connected = ref(false)
  const retryCount = ref(0)

  let ws: WebSocket | null = null
  const handlers: Map<string, MessageHandler[]> = new Map()
  let reconnectTimer: number | null = null
  let allowReconnect = reconnect

  // ---- 连接 ----

  function connect() {
    if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) return

    allowReconnect = reconnect
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    const socket = new WebSocket(url)
    ws = socket

    socket.onopen = () => {
      if (ws !== socket) return
      connected.value = true
      retryCount.value = 0
      console.log('[WS] 已连接')
    }

    socket.onclose = () => {
      if (ws !== socket) return
      ws = null
      connected.value = false
      console.log('[WS] 断开')
      if (allowReconnect && retryCount.value < maxRetries && reconnectTimer === null) {
        const delay = Math.min(1000 * 2 ** retryCount.value, 10000)
        console.log(`[WS] ${delay}ms 后重连...`)
        reconnectTimer = window.setTimeout(() => {
          reconnectTimer = null
          retryCount.value++
          connect()
        }, delay)
      }
    }

    socket.onerror = (e) => {
      console.error('[WS] 错误', e)
    }

    socket.onmessage = (event) => {
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
    allowReconnect = false
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    const socket = ws
    ws = null
    connected.value = false
    socket?.close()
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
