# Requirements Document

## Introduction

本文档定义「设备管理主页（Device Home Dashboard）」功能的需求。该功能在现有小橙控制面板之前增加一个类似米家 App 的设备管理首页，作为所有智能硬件设备的统一入口。用户打开前端后首先看到设备列表，可以查看每台设备的在线状态、电量等关键信息，执行远程唤醒操作，并选择进入某台设备的专属控制面板（如小橙的摇杆/摄像头/灯光控制界面）。

当前系统直接进入小橙控制面板，没有设备选择层。本功能引入设备注册表、状态探测、路由导航三大能力，为未来管理多台异构硬件设备奠定架构基础。

## Glossary

- **Dashboard**: 设备管理主页，展示所有已注册设备的卡片列表，是前端应用的首屏
- **Device_Registry**: 设备注册表，存储所有已注册设备的元数据（名称、类型、地址、图标等）的持久化数据源
- **Device_Card**: 设备卡片，Dashboard 上代表单个设备的 UI 组件，展示设备名称、类型图标、在线状态和关键指标
- **Status_Prober**: 状态探测器，后端定时轮询各设备可达性和关键指标（在线/离线、电量等）的服务
- **WOL_Service**: Wake-on-LAN 服务，通过发送魔术包（Magic Packet）远程唤醒支持 WOL 的设备
- **Control_Panel**: 设备控制面板，某台设备的专属操作界面（如小橙的摇杆、摄像头、灯光面板）
- **Router**: 前端路由模块，管理 Dashboard 与各设备 Control_Panel 之间的页面导航
- **Device_Store**: 前端 Pinia 状态仓库，缓存设备列表和实时状态数据供 UI 组件消费

## Requirements

### Requirement 1: 设备注册与持久化

**User Story:** As a 用户, I want to 注册和管理我的硬件设备列表, so that 系统知道我拥有哪些设备并能持续追踪它们。

#### Acceptance Criteria

1. THE Device_Registry SHALL 以 JSON 配置文件形式存储设备列表，每条记录包含设备 ID、名称、类型、IP 地址、MAC 地址和图标标识
2. WHEN 后端启动时, THE Device_Registry SHALL 从配置文件加载所有已注册设备并在内存中维护设备列表
3. WHEN 配置文件不存在或为空时, THE Device_Registry SHALL 创建包含小橙（XiaoCheng）作为默认设备的初始配置
4. THE Device_Registry SHALL 为每台设备分配唯一的设备 ID（UUID 格式）
5. WHEN 通过 HTTP API 添加新设备时, THE Device_Registry SHALL 验证必填字段（名称、类型、IP 地址）并将设备持久化到配置文件
6. WHEN 通过 HTTP API 删除设备时, THE Device_Registry SHALL 从配置文件中移除该设备记录
7. IF 配置文件格式无效, THEN THE Device_Registry SHALL 记录错误日志并回退到默认配置

### Requirement 2: 设备状态探测

**User Story:** As a 用户, I want to 实时了解每台设备的在线状态和关键指标, so that 我能快速判断哪些设备可用。

#### Acceptance Criteria

1. THE Status_Prober SHALL 每 10 秒对所有已注册设备执行一次可达性探测
2. WHEN 探测目标设备时, THE Status_Prober SHALL 通过 HTTP 请求目标设备的 `/api/status` 端点判断设备是否在线
3. WHEN 设备的 `/api/status` 端点在 3 秒内返回有效响应时, THE Status_Prober SHALL 将该设备标记为在线（online）
4. WHEN 设备的 `/api/status` 端点在 3 秒内未返回有效响应时, THE Status_Prober SHALL 将该设备标记为离线（offline）
5. WHEN 设备在线且 `/api/status` 返回电量信息时, THE Status_Prober SHALL 提取并缓存该设备的电池电量百分比和电压值
6. WHEN 设备状态从在线变为离线或从离线变为在线时, THE Status_Prober SHALL 记录状态变更日志
7. THE Status_Prober SHALL 通过 HTTP API（`GET /api/devices`）向前端提供所有设备的最新状态快照

### Requirement 3: 远程唤醒（Wake-on-LAN）

**User Story:** As a 用户, I want to 从 Dashboard 远程唤醒处于关机或休眠状态的设备, so that 我不需要物理接触设备即可开机。

#### Acceptance Criteria

1. WHEN 用户对一台离线设备触发唤醒操作时, THE WOL_Service SHALL 向该设备的 MAC 地址发送符合 IEEE 标准的 Wake-on-LAN 魔术包（Magic Packet）
2. WHEN 魔术包发送成功时, THE WOL_Service SHALL 返回发送成功的确认信息
3. IF 设备未配置 MAC 地址, THEN THE WOL_Service SHALL 返回错误信息说明该设备不支持远程唤醒
4. WHEN 唤醒操作触发后, THE Status_Prober SHALL 在随后的 60 秒内以 5 秒间隔对该设备执行加速探测
5. IF 魔术包发送失败（网络异常等）, THEN THE WOL_Service SHALL 返回包含失败原因的错误信息

### Requirement 4: Dashboard 前端界面

**User Story:** As a 用户, I want to 在一个美观的主页上以卡片形式浏览所有设备, so that 我能一目了然地掌握所有设备的状态。

#### Acceptance Criteria

1. THE Dashboard SHALL 以网格布局展示所有已注册设备的 Device_Card
2. THE Device_Card SHALL 展示设备名称、设备类型图标、在线/离线状态指示器和电池电量（如有）
3. WHEN 设备处于在线状态时, THE Device_Card SHALL 以绿色圆点和「在线」文字标识在线状态
4. WHEN 设备处于离线状态时, THE Device_Card SHALL 以灰色圆点和「离线」文字标识离线状态，并将卡片整体降低不透明度
5. WHEN 设备拥有电池电量数据时, THE Device_Card SHALL 展示电池图标和电量百分比数值
6. THE Dashboard SHALL 在页面顶部展示标题栏，包含应用名称和设备数量统计
7. THE Dashboard SHALL 采用与现有控制面板一致的深色主题（背景色 #0d0f14、主色调 #e8842c）
8. WHEN 设备列表正在加载时, THE Dashboard SHALL 展示加载骨架屏（Skeleton）占位
9. WHEN 设备列表为空时, THE Dashboard SHALL 展示空状态提示信息引导用户添加设备

### Requirement 5: 设备卡片交互

**User Story:** As a 用户, I want to 通过设备卡片快速执行常用操作, so that 我能高效地管理和控制设备。

#### Acceptance Criteria

1. WHEN 用户点击一张在线设备的 Device_Card 时, THE Router SHALL 导航到该设备的 Control_Panel 页面
2. WHEN 用户点击一张离线设备的 Device_Card 时, THE Dashboard SHALL 展示该设备的操作菜单，包含「远程唤醒」选项（如设备支持 WOL）
3. WHEN 用户在操作菜单中点击「远程唤醒」时, THE Dashboard SHALL 调用 WOL_Service 发送唤醒请求并在 Device_Card 上展示「唤醒中...」状态
4. WHILE 设备处于唤醒等待状态时, THE Device_Card SHALL 展示脉冲动画指示正在等待设备上线
5. WHEN 唤醒后设备成功上线时, THE Device_Card SHALL 自动更新为在线状态并移除唤醒动画
6. IF 唤醒请求失败, THEN THE Dashboard SHALL 展示 Toast 提示告知用户唤醒失败及原因

### Requirement 6: 前端路由与导航

**User Story:** As a 用户, I want to 在设备主页和各设备控制面板之间自由切换, so that 我能方便地管理多台设备。

#### Acceptance Criteria

1. THE Router SHALL 将根路径（`/`）映射到 Dashboard 页面
2. THE Router SHALL 将 `/device/:id` 路径映射到对应设备的 Control_Panel 页面
3. WHEN 用户从 Dashboard 进入某设备的 Control_Panel 时, THE Router SHALL 在 Control_Panel 顶部提供返回 Dashboard 的导航按钮
4. WHEN 用户点击返回按钮时, THE Router SHALL 导航回 Dashboard 页面并保留之前的设备状态数据
5. THE Router SHALL 将现有的小橙控制面板（App.vue 当前内容）封装为 `/device/xiaocheng` 路由对应的 Control_Panel 组件
6. IF 用户访问不存在的设备路径, THEN THE Router SHALL 重定向到 Dashboard 页面

### Requirement 7: 设备状态实时更新

**User Story:** As a 用户, I want to Dashboard 上的设备状态能自动刷新, so that 我看到的信息始终是最新的。

#### Acceptance Criteria

1. WHEN Dashboard 页面加载完成时, THE Device_Store SHALL 立即从后端 API 获取完整的设备列表和状态数据
2. THE Device_Store SHALL 每 10 秒从后端 API 轮询最新的设备状态数据
3. WHEN 收到新的状态数据时, THE Device_Store SHALL 更新内存中的设备状态并触发 UI 响应式更新
4. WHEN 用户从 Control_Panel 返回 Dashboard 时, THE Device_Store SHALL 立即执行一次状态刷新
5. IF 状态轮询请求失败, THEN THE Device_Store SHALL 保留上一次成功获取的数据并在下一个周期重试

### Requirement 8: 后端设备管理 API

**User Story:** As a 前端开发者, I want to 通过 RESTful API 管理设备和查询状态, so that 前端能与后端解耦地交互。

#### Acceptance Criteria

1. THE Device_Registry SHALL 通过 `GET /api/devices` 端点返回所有设备及其最新状态的 JSON 数组
2. THE Device_Registry SHALL 通过 `POST /api/devices` 端点接受新设备注册请求
3. THE Device_Registry SHALL 通过 `DELETE /api/devices/{id}` 端点接受设备删除请求
4. THE WOL_Service SHALL 通过 `POST /api/devices/{id}/wake` 端点接受远程唤醒请求
5. WHEN API 请求参数校验失败时, THE Device_Registry SHALL 返回 HTTP 422 状态码和描述性错误信息
6. WHEN 请求的设备 ID 不存在时, THE Device_Registry SHALL 返回 HTTP 404 状态码
