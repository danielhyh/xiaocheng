---
title: WebSocket 接口
scope: WS envelope 解析 + 路由，协议契约层
code: app/api/websocket.py
last_verified: 2026-06-25
decisions: [ADR-003, ADR-004]
---
# WebSocket 接口

## 职责
维护 WS 连接，解析统一 envelope `{ type, ts, payload }`，把 `cmd.*` 路由到 dispatcher，向客户端推送 `tel.*` / `event.*`。

## 关键实现 / 注意事项
- type 点号分层：`cmd.*`（指令）/ `tel.*`（遥测）/ `event.*`（事件）。
- 新增功能只加新 type，协议层零改动（见 ADR-004）。
- 连接生命周期与 safety Watchdog 绑定，断连触发停车。
