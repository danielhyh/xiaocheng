# Implementation Plan: Device Home Dashboard

## Overview

前端优先开发策略：先用 mock 数据完成全部前端 UI 和交互，再实现后端设备管理服务，最后集成联调。前端使用 Vue Router 4 实现路由导航，Pinia 管理设备状态，科技风深色主题贯穿所有组件。后端在现有 FastAPI 应用上扩展设备注册表、状态探测和 WOL 服务。

## Tasks

- [-] 1. 前端基础设施搭建
  - [ ] 1.1 安装 Vue Router 4 依赖并配置路由
    - 在 `frontend/` 下安装 `vue-router@4`
    - 创建 `frontend/src/router/index.ts`，定义路由表：`/` → DashboardPage，`/device/:id` → DeviceControlPage，`*` → 重定向到 `/`
    - 修改 `frontend/src/main.ts`，注册 router 插件
    - _Requirements: 6.1, 6.2, 6.6_

  - [ ] 1.2 定义前端 TypeScript 类型
    - 创建 `frontend/src/types/device.ts`，定义 `Device`、`CreateDeviceRequest`、`WakeResponse` 接口（按设计文档 Data Models 章节）
    - _Requirements: 4.2, 8.1_

  - [ ] 1.3 创建科技风 CSS 变量和全局样式
    - 创建 `frontend/src/styles/variables.css`，包含设计文档中的完整色彩系统（`--bg-base`、`--tech-cyan`、`--brand` 等）
    - 创建 `frontend/src/styles/animations.css`，包含唤醒脉冲、呼吸灯、骨架屏闪烁、卡片入场动画
    - 在 `frontend/src/main.ts` 中引入全局样式文件
    - _Requirements: 4.7_

- [ ] 2. 前端 Store 和 API Composable（含 mock 数据）
  - [ ] 2.1 创建 useDeviceApi composable（含 mock 实现）
    - 创建 `frontend/src/composables/useDeviceApi.ts`
    - 实现 `fetchDevices()`、`wakeDevice(id)`、`addDevice(data)`、`deleteDevice(id)` 方法
    - 内置 mock 数据（小橙在线 + 门口摄像头离线），开发模式下直接返回 mock 数据，生产模式调用真实 API
    - 使用环境变量或 `import.meta.env.DEV` 切换 mock/real 模式
    - _Requirements: 7.1, 8.1, 8.2, 8.3, 8.4_

  - [ ] 2.2 创建 deviceStore（Pinia）
    - 创建 `frontend/src/stores/deviceStore.ts`
    - 实现 state：`devices`、`isLoading`、`lastFetchTime`
    - 实现 actions：`fetchDevices()`（调用 useDeviceApi）、`wakeDevice(id)`（调用 WOL API 并设置 waking 状态）、`startPolling()`（10 秒间隔轮询）、`stopPolling()`
    - 轮询失败时保留上次数据，下个周期重试
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 3. 前端 UI 组件 — Dashboard 页面
  - [ ] 3.1 实现 DashboardHeader 组件
    - 创建 `frontend/src/components/dashboard/DashboardHeader.vue`
    - 展示应用名称「设备管理」、设备总数和在线数量统计
    - 科技风样式：深色背景、`--tech-cyan` 强调色、底部发光分隔线
    - _Requirements: 4.6_

  - [ ] 3.2 实现 DeviceCardSkeleton 骨架屏组件
    - 创建 `frontend/src/components/dashboard/DeviceCardSkeleton.vue`
    - 模拟 DeviceCard 布局的占位动画，使用 `skeleton-shimmer` 动画
    - _Requirements: 4.8_

  - [ ] 3.3 实现 EmptyState 空状态组件
    - 创建 `frontend/src/components/dashboard/EmptyState.vue`
    - 展示空状态图标和引导文字「暂无设备，请添加您的第一台设备」
    - _Requirements: 4.9_

  - [ ] 3.4 实现 BatteryIndicator 电量指示器组件
    - 创建 `frontend/src/components/dashboard/BatteryIndicator.vue`
    - 大号数字显示电量百分比（JetBrains Mono 字体、36px、`--tech-cyan` 色 + text-shadow 发光）
    - 电压副指标（14px、`--text-secondary`）
    - 根据 `level` 属性切换颜色：ok → cyan、low → warning、critical → error
    - _Requirements: 4.5_

  - [ ] 3.5 实现 WakeButton 唤醒按钮组件
    - 创建 `frontend/src/components/dashboard/WakeButton.vue`
    - 支持 idle / waking / success / failed 四种状态
    - waking 状态展示脉冲动画（`wake-pulse` keyframes）
    - 不支持 WOL 的设备隐藏按钮
    - _Requirements: 5.3, 5.4_

  - [ ] 3.6 实现 DeviceCard 设备卡片组件
    - 创建 `frontend/src/components/dashboard/DeviceCard.vue`
    - 展示设备名称、类型图标、在线/离线状态指示器（绿色/灰色圆点 + 文字）
    - 在线卡片：毛玻璃背景 + 青蓝边框 + 微弱发光 box-shadow
    - 离线卡片：`opacity: 0.55`、边框降低亮度
    - 悬停效果：边框亮度提升 + `translateY(-2px)`
    - 集成 BatteryIndicator 和 WakeButton 子组件
    - 在线设备点击 → emit `click` 事件；离线设备点击 → 展示唤醒操作
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2_

  - [ ] 3.7 实现 DashboardPage 主页面
    - 创建 `frontend/src/pages/DashboardPage.vue`
    - 组装 DashboardHeader、DeviceCard 网格、DeviceCardSkeleton、EmptyState
    - 页面加载时调用 `deviceStore.fetchDevices()` 并启动轮询
    - 离开页面时停止轮询
    - 根据 isLoading / devices.length 切换骨架屏 / 空状态 / 卡片网格
    - 在线设备点击 → 路由到 `/device/:id`；离线设备唤醒 → 调用 `deviceStore.wakeDevice()`
    - 唤醒失败时展示 Toast 提示
    - 卡片入场使用 `card-enter` 动画
    - _Requirements: 4.1, 4.8, 4.9, 5.1, 5.2, 5.3, 5.5, 5.6, 7.1, 7.2_

- [ ] 4. Checkpoint — 前端 Dashboard 页面验收
  - 确保所有 Dashboard 组件可正常渲染（使用 mock 数据），卡片样式符合科技风规范，骨架屏和空状态正确切换。如有问题请向用户确认。

- [ ] 5. 前端路由集成与现有面板封装
  - [ ] 5.1 封装现有控制面板为 XiaoChengPanel 组件
    - 创建 `frontend/src/components/panels/XiaoChengPanel.vue`
    - 将 `App.vue` 中现有的控制面板逻辑（WebSocket 连接、摇杆、摄像头、功能按钮、各面板）迁移到此组件
    - 保持所有现有功能不变
    - _Requirements: 6.5_

  - [ ] 5.2 实现 DeviceControlPage 页面
    - 创建 `frontend/src/pages/DeviceControlPage.vue`
    - 顶部 ControlPageHeader：返回按钮 + 设备名称
    - 根据路由参数 `:id` 加载对应设备的控制面板（当前仅小橙 → XiaoChengPanel）
    - 不存在的设备 ID → 重定向到 Dashboard
    - _Requirements: 6.2, 6.3, 6.6_

  - [ ] 5.3 重构 App.vue 为路由容器
    - 将 `App.vue` 简化为路由容器：仅包含 `<router-view />`
    - 全局样式保留在 App.vue 或全局样式文件中
    - 确保从 DeviceControlPage 返回 Dashboard 时保留设备状态数据
    - _Requirements: 6.4, 7.4_

- [ ] 6. Checkpoint — 前端路由与导航验收
  - 确保路由导航正常工作：Dashboard ↔ DeviceControlPage 切换流畅，现有小橙控制面板功能完整保留，返回按钮和状态保持正确。如有问题请向用户确认。

- [ ] 7. 后端数据模型与设备注册表
  - [ ] 7.1 创建 Pydantic 数据模型
    - 创建 `app/device/__init__.py` 和 `app/device/models.py`
    - 定义 `DeviceType` 枚举、`DeviceRecord`、`DeviceStatus`、`DeviceResponse`、`CreateDeviceRequest`、`WakeResponse` 模型（按设计文档 Data Models 章节）
    - _Requirements: 1.1, 8.5_

  - [ ] 7.2 实现 DeviceRegistry 设备注册表
    - 创建 `app/device/registry.py`
    - 实现 `load()` / `save()` — 从 `app/data/devices.json` 加载/持久化设备列表
    - 实现 `list_all()` / `get()` / `add()` / `remove()` CRUD 方法
    - 文件不存在时创建默认配置（含小橙作为默认设备）
    - JSON 格式无效时记录错误日志并回退默认配置
    - 添加设备时验证必填字段并分配 UUID
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [ ] 7.3 创建默认设备配置文件
    - 创建 `app/data/devices.json`，包含小橙作为默认设备的初始数据
    - _Requirements: 1.3_

- [ ] 8. 后端状态探测与 WOL 服务
  - [ ] 8.1 实现 StatusProber 状态探测器
    - 创建 `app/device/prober.py`
    - 实现 `start()` / `stop()` — 后台 asyncio 任务，每 10 秒轮询所有设备
    - 实现 `probe_device()` — HTTP GET 目标设备 `/api/status`，3 秒超时
    - 在线时提取电量信息缓存；超时或异常标记离线
    - 实现 `accelerated_probe()` — WOL 后 60 秒内以 5 秒间隔加速探测
    - 状态变更时记录日志
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [ ] 8.2 实现 WOLService 远程唤醒服务
    - 创建 `app/device/wol.py`
    - 实现 `build_magic_packet(mac)` — 构建 102 字节魔术包（6×0xFF + 16×MAC）
    - 实现 `send_wol(mac)` — UDP 广播发送魔术包
    - 无 MAC 地址时返回错误信息
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [ ] 9. 后端 API 端点与生命周期集成
  - [ ] 9.1 实现设备管理 HTTP API
    - 创建 `app/api/device.py`
    - 实现 `GET /api/devices` — 返回所有设备及最新状态
    - 实现 `POST /api/devices` — 添加新设备（422 校验失败）
    - 实现 `DELETE /api/devices/{id}` — 删除设备（404 不存在）
    - 实现 `POST /api/devices/{id}/wake` — 远程唤醒（触发加速探测）
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 3.4_

  - [ ] 9.2 集成到 FastAPI 应用生命周期
    - 修改 `app/main.py`，在 lifespan 中初始化 DeviceRegistry、StatusProber
    - 注册 device API router
    - 启动时加载设备注册表、启动状态探测后台任务
    - 关闭时停止探测任务
    - _Requirements: 1.2, 2.1_

- [ ] 10. Checkpoint — 后端 API 验收
  - 确保所有后端 API 端点正常工作，设备注册表 CRUD、状态探测、WOL 发送均可通过 HTTP 测试。如有问题请向用户确认。

- [ ] 11. 前后端集成
  - [ ] 11.1 切换前端 API 到真实后端
    - 修改 `useDeviceApi.ts`，将 mock 模式切换逻辑完善：开发模式（无后端）使用 mock，有后端时调用真实 `/api/devices` 等端点
    - 确保 Vite proxy 配置已覆盖 `/api/devices` 路径（现有 `/api` proxy 已覆盖）
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 11.2 端到端功能验证
    - 验证 Dashboard 加载真实设备列表
    - 验证设备状态轮询更新
    - 验证 WOL 唤醒流程（发送 → 等待 → 状态更新）
    - 验证路由导航：Dashboard → 小橙控制面板 → 返回 Dashboard
    - _Requirements: 5.5, 7.3, 7.4_

- [ ] 12. 后端属性测试
  - [ ]* 12.1 Write property test for DeviceRecord serialization round-trip
    - **Property 1: Device record serialization round-trip**
    - 使用 Hypothesis 生成任意合法 DeviceRecord，验证 JSON 序列化/反序列化后字段完全一致
    - 创建 `tests/test_device_properties.py`
    - **Validates: Requirements 1.1**

  - [ ]* 12.2 Write property test for Device ID uniqueness
    - **Property 2: Device IDs are unique and UUID-formatted**
    - 使用 Hypothesis 生成 N 个设备创建请求，验证所有分配的 ID 唯一且符合 UUID 格式
    - **Validates: Requirements 1.4**

  - [ ]* 12.3 Write property test for device creation input validation
    - **Property 3: Device creation input validation**
    - 使用 Hypothesis 生成合法和非法的 CreateDeviceRequest，验证注册表正确接受/拒绝
    - **Validates: Requirements 1.5, 8.5**

  - [ ]* 12.4 Write property test for delete preserves other devices
    - **Property 4: Delete preserves other devices**
    - 使用 Hypothesis 生成包含 N 个设备的注册表，删除一个后验证剩余 N-1 个设备不变
    - **Validates: Requirements 1.6**

  - [ ]* 12.5 Write property test for WOL magic packet structure
    - **Property 5: WOL magic packet structure**
    - 使用 Hypothesis 生成任意合法 MAC 地址，验证魔术包为 102 字节且结构正确
    - **Validates: Requirements 3.1**

  - [ ]* 12.6 Write property test for status response battery data extraction
    - **Property 6: Status response battery data extraction**
    - 使用 Hypothesis 生成 battery_percent (0-100) 和 battery_voltage (0.0-12.0)，验证 StatusProber 正确提取缓存
    - **Validates: Requirements 2.5**

- [ ] 13. Final checkpoint — 全部测试通过
  - 确保所有测试通过，前后端集成正常，如有问题请向用户确认。

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- 前端任务（1-6）可独立于后端开发，使用 mock 数据驱动
- 后端任务（7-10）不影响现有控制面板功能
- 属性测试使用 pytest + hypothesis，每个属性 `@settings(max_examples=100)`
- 现有 Vite proxy 配置已覆盖 `/api` 前缀，无需额外配置
- JetBrains Mono 字体需在 `index.html` 中通过 Google Fonts 引入
