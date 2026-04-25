# 仓库协作指南

## 语言约定

- 始终使用中文响应用户，除非用户明确要求使用其他语言。

## 项目概览

小橙是一个 4WD 智能小车控制栈。后端是 FastAPI 应用，提供 HTTP、WebSocket 控制接口和摄像头流占位接口。前端是 Vue 3 + Pinia + Vite 控制面板。电机硬件封装在 `app/drivers/motor` 后面，通过 `XIAOCHENG_MOCK=1` 选择 mock 实现，便于在 PC 上开发和测试。

## 目录结构

- `app/main.py` 组装 FastAPI 应用、生命周期、子系统、业务服务和路由。
- `app/config.py` 集中维护板级常量、电机引脚/PWM 设置、WebSocket 时间参数和遥测间隔。
- `app/api/` 包含 HTTP、WebSocket 和 stream 路由。
- `app/business/` 包含命令分发、模式状态、安全看门狗和遥测发布。
- `app/subsystems/motion.py` 将归一化摇杆命令 `vx`、`vy` 转换为左右电机速度。
- `app/drivers/motor/` 根据 `config.USE_MOCK` 选择 `mock.py` 或 `real.py`。
- `frontend/src/` 包含 Vue 应用、UI 组件、WebSocket composable 和 Pinia store。
- `tests/` 当前主要覆盖运动映射行为。

## 运行命令

在仓库根目录运行后端测试：

```powershell
$env:XIAOCHENG_MOCK = "1"
python -m pytest tests/ -v
```

PC/mock 模式启动后端：

```powershell
$env:XIAOCHENG_MOCK = "1"
uvicorn app.main:app --reload
```

启动前端：

```powershell
Set-Location frontend
npm run dev
```

开发板运行方式，需先安装 `wiringpi` 等板端依赖：

```powershell
uvicorn app.main:app --host 0.0.0.0
```

## 开发注意事项

- 本地开发和测试默认使用 mock 模式，除非任务明确要求验证 Orange Pi 硬件行为。
- 硬件相关改动应尽量限制在 driver/subsystem 边界内；上层代码应依赖接口和子系统方法，而不是直接依赖 GPIO/PWM 细节。
- WebSocket 消息使用 envelope 结构：`type`、`ts`、可选 `id` 和 `payload`。
- 新增命令族通常需要增加子系统/驱动、注册 dispatcher handler，并更新前端组件或 store。
- 源码注释和文档大多是中文 UTF-8。如果 PowerShell 显示乱码，优先使用 UTF-8 工具读取，或先调整终端代码页后再判断文件内容。
- `frontend/node_modules` 已存在于工作区；除非确实要排查依赖问题，否则避免扫描或编辑它。

## 验证方式

- 后端逻辑改动：设置 `XIAOCHENG_MOCK=1` 后运行 `python -m pytest tests/ -v`。
- 前端改动：在 `frontend` 目录运行 `npm run build`。
- 如果修改 WebSocket 协议，同时检查 `app/api/websocket.py`、`app/business/dispatcher.py` 和 `frontend/src/composables/useWebSocket.ts`。
