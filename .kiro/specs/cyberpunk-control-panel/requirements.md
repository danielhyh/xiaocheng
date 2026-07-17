# Requirements Document

## Introduction

`cyberpunk-control-panel`（以下简称「赛博朋克控制面板」）是小橙前端的全新视觉层，以手机横屏为基线（812×375）重构控制界面，向上兼容 iPad 与 PC，并保留旧组件作为回退。本特性仅替换/新增前端视觉与交互层，后端协议、`carStore` 数据模型、WebSocket envelope 与所有子系统均不变更。

本次交付的核心目标：

1. 建立 Tailwind CSS v4 + 官方 Vite 插件的样式骨架，并在 `frontend/src/cyberpunk/` 下落地七大区域的全套新组件。
2. 以纯 CSS 渐变、SVG、占位块完成首轮视觉，所有位图素材仅登记规格、**不**在本特性内实装。
3. 保证操作手感不弱于旧面板：虚拟摇杆 100ms 保活、BRAKE 100ms 循环、HORN 短按/长按区分、弹框外部点击关闭、竖屏旋转提示。
4. 电量展示完全遵循后端 `battery_level` 枚举（`ok` / `low` / `critical` / `unknown`），前端不硬编码电压阈值；`critical` 时以 0.8s 红色呼吸提示风险。
5. 关键交互逻辑（摇杆归一化、电量分档、BRAKE 保护窗口、弹框外部点击）定义可执行的正确性属性，便于后续 PBT 覆盖。

## Glossary

- **CyberpunkPanel**：新赛博朋克控制面板的顶层 Vue 视图，挂载在既有前端路由/入口，替换旧布局。
- **HUDBar**：位于屏幕顶部的状态条，展示模式、电量、信号、延迟、FPS、时间。
- **FPVStage**：中央 MJPEG 视频显示层，铺满可视区。
- **ReversePiP**：左上角倒车画中画小窗，后视摄像头或后视裁剪流的占位位置。
- **MoveJoystick**：左下角虚拟移动摇杆，输出归一化向量 `(vx, vy)`。
- **GimbalJoystick**：右下角云台摇杆，输出归一化角度增量 `(pan, tilt)`。
- **BrakeButton**：右下角 BRAKE 按钮，按住循环发送 `cmd.brake`。
- **HornButton**：右下角 HORN 按钮，短按/长按区分触发音效。
- **FloatingActionGroup**：屏幕右侧悬浮的 3 按钮竖列，用于切换灯光 / 音响 / 模式等面板。
- **DataBar**：底部数据条，展示速度、朝向、超声测距等运行时数值。
- **LightPopover**：灯光弹框，包含大灯开关、亮度滑块、灯带模式。
- **AudioPopover**：音响弹框，包含音量、麦克风、TTS 输入。
- **ModeSwitch**：模式切换控件，前端两档：`手动` 与 `智能`。
- **OrientationGuard**：竖屏旋转提示遮罩。
- **BatteryIndicator**：HUDBar 中的电量子组件。
- **KeepaliveService**：前端运动指令 100ms 重发定时器。
- **CarStore**：现有 `frontend/src/stores/carStore.ts` Pinia store。
- **LegacyPanel**：现有 `frontend/src/components/` 下的旧组件集合，保留为回退选项。
- **BatteryLevel**：`CarStore.sensors.battery_level`，取值域 `{ok, low, critical, unknown}`。
- **BaselineViewport**：基线视口尺寸 812×375（手机横屏）。
- **TouchMinSize**：最小触控命中尺寸 44×44 CSS 像素。

## Requirements

### Requirement 1 — 样式骨架与目录基线

**User Story:** 作为前端开发者，我希望在项目中引入 Tailwind CSS v4 并建立独立目录，以便新面板与旧组件互不干扰。

#### Acceptance Criteria

1. THE CyberpunkPanel SHALL 通过 Tailwind CSS v4 与其官方 Vite 插件提供样式能力，并在 `frontend/vite.config.ts` 中注册该插件。
2. THE CyberpunkPanel SHALL 将全部新组件、样式与工具函数放置于 `frontend/src/cyberpunk/` 目录下。
3. THE CyberpunkPanel SHALL 保留 `frontend/src/components/` 下的 LegacyPanel 组件文件不被删除或移动。
4. WHEN 构建执行 `npm run build`，THE CyberpunkPanel SHALL 在不修改后端任何文件的前提下通过构建。
5. WHERE 项目启用赛博朋克面板，THE CyberpunkPanel SHALL 作为默认挂载视图，LegacyPanel 仅作为可回退的备用入口。

### Requirement 2 — 横屏基线与多端适配

**User Story:** 作为手机驾驶员，我希望面板在横屏下铺满、在竖屏下提示旋转，以保持一致的操控布局。

#### Acceptance Criteria

1. THE CyberpunkPanel SHALL 以 BaselineViewport（812×375）作为布局基线，并在该尺寸下呈现所有七大区域（HUDBar、FPVStage、MoveJoystick、GimbalJoystick+BrakeButton+HornButton、FloatingActionGroup、DataBar、ReversePiP）。
2. WHEN 视口宽高比 `width/height < 1`，THE OrientationGuard SHALL 覆盖全屏并提示用户旋转到横屏。
3. WHILE OrientationGuard 处于激活状态，THE CyberpunkPanel SHALL 暂停所有控制交互（摇杆、按钮、弹框）。
4. WHERE 视口的较短边 ≥ 600 CSS 像素（iPad 档），THE CyberpunkPanel SHALL 在保持七大区域相对位置的前提下按比例放大。
5. WHERE 视口的较短边 ≥ 900 CSS 像素（PC 档），THE CyberpunkPanel SHALL 在保持七大区域相对位置的前提下按比例放大并允许外围留黑边。
6. THE CyberpunkPanel SHALL 保证所有可触控元素的命中矩形不小于 TouchMinSize（44×44 CSS 像素）。

### Requirement 3 — 顶部 HUD 状态条

**User Story:** 作为驾驶员，我希望一眼看到车辆的关键状态，以便快速判断是否继续操控。

#### Acceptance Criteria

1. THE HUDBar SHALL 固定在屏幕顶部并横跨全宽。
2. THE HUDBar SHALL 显示以下字段：`CarStore.mode`、`CarStore.sensors.battery_level`、`CarStore.sensors.wifi_rssi`、`CarStore.wsLatency`、FPV 当前 FPS、本地时间（HH:mm）。
3. WHEN `CarStore.connected` 为 `false`，THE HUDBar SHALL 在延迟位置显示「离线」占位文本而不是数值。
4. THE HUDBar SHALL 在每次 CarStore 对应字段变化后 ≤ 200ms 内完成视图更新。

### Requirement 4 — 中央 FPV 视觉层

**User Story:** 作为驾驶员，我希望视频画面作为视觉中心且带有赛博朋克质感装饰，以获得沉浸感。

#### Acceptance Criteria

1. THE FPVStage SHALL 铺满 CyberpunkPanel 的主背景层并位于所有控件之下。
2. THE FPVStage SHALL 直接复用现有后端 MJPEG 接口 `/stream/camera` 并在图像加载失败时显示离线占位块。
3. THE FPVStage SHALL 叠加 CSS 扫描线动画与十字准星，并且叠加层不拦截指针事件。
4. WHILE FPVStage 处于离线占位状态，THE FPVStage SHALL 每 3000ms 尝试重新加载一次 MJPEG 源。

### Requirement 5 — 倒车画中画

**User Story:** 作为驾驶员，我希望倒车时后视画面自动放大，以便安全倒车。

#### Acceptance Criteria

1. THE ReversePiP SHALL 默认以缩略尺寸显示在左上角（基线下宽度不超过视口宽度的 25%）。
2. WHEN `CarStore.motion.vy < 0`，THE ReversePiP SHALL 放大至基线下宽度不小于视口宽度的 40%。
3. WHEN `CarStore.motion.vy ≥ 0`，THE ReversePiP SHALL 恢复为默认缩略尺寸。
4. THE ReversePiP SHALL 在切换尺寸时使用不超过 300ms 的过渡动画。
5. WHERE 后端未提供独立后视流，THE ReversePiP SHALL 使用占位渲染（CSS 渐变 + 文本 `REAR CAM`）。

### Requirement 6 — 左下虚拟移动摇杆

**User Story:** 作为驾驶员，我希望用左手拇指连续控制前后左右，以便平滑驾驶。

#### Acceptance Criteria

1. THE MoveJoystick SHALL 渲染为外圆直径 120 CSS 像素、内圆点可拖拽的控件，并固定在屏幕左下角。
2. WHILE 用户按下并拖动 MoveJoystick，THE MoveJoystick SHALL 以 `(vx, vy) = clampToUnitDisk(dx / R, dy / R)` 计算归一化向量，其中 `R` 为外圆半径，`dx, dy` 为指针相对外圆圆心的偏移量。
3. WHILE 用户持续按住 MoveJoystick，THE KeepaliveService SHALL 每 100 ± 20 ms 发送一次 `cmd.motion`，payload 为当前 `(vx, vy)`。
4. WHEN 用户释放 MoveJoystick，THE MoveJoystick SHALL 立即将内圆点回中，并发送一次 `(vx, vy) = (0, 0)` 的 `cmd.motion`。
5. THE MoveJoystick SHALL 保证输出向量满足 `vx² + vy² ≤ 1 + 1e-6`。
6. IF 指针在 MoveJoystick 外被抬起或丢失（`pointercancel` / `pointerleave`），THEN THE MoveJoystick SHALL 按照释放流程回中并发送 `(0, 0)`。

### Requirement 7 — 右下云台摇杆

**User Story:** 作为驾驶员，我希望用右手拇指控制云台视角，以便观察环境。

#### Acceptance Criteria

1. THE GimbalJoystick SHALL 渲染为与 MoveJoystick 对称的外圆直径 120 CSS 像素摇杆，固定在屏幕右下角。
2. WHILE 用户拖动 GimbalJoystick，THE GimbalJoystick SHALL 以 `(pan, tilt) = clampToUnitDisk(dx / R, dy / R)` 计算归一化向量。
3. WHILE 用户持续按住 GimbalJoystick，THE KeepaliveService SHALL 每 100 ± 20 ms 发送一次 `cmd.gimbal`，payload 以 pan/tilt 归一化向量形式提交。
4. WHEN 用户释放 GimbalJoystick，THE GimbalJoystick SHALL 立即将内圆点回中，并停止发送 `cmd.gimbal`。
5. THE GimbalJoystick SHALL 保证输出向量满足 `pan² + tilt² ≤ 1 + 1e-6`。

### Requirement 8 — BRAKE 与 HORN

**User Story:** 作为驾驶员，我希望有可按压循环的刹车和可短/长按的鸣笛按钮，以应对紧急场景。

#### Acceptance Criteria

1. THE BrakeButton SHALL 位于屏幕右下角、与 GimbalJoystick 同侧，命中区域不小于 TouchMinSize。
2. WHILE 用户按住 BrakeButton，THE BrakeButton SHALL 以 100 ± 20 ms 的周期循环发送 `cmd.brake`，首帧 SHALL 在 `pointerdown` 事件后 ≤ 20 ms 内发送。
3. WHEN 用户释放 BrakeButton（`pointerup` / `pointercancel` / `pointerleave`），THE BrakeButton SHALL 立即停止发送 `cmd.brake`。
4. THE HornButton SHALL 位于 BrakeButton 附近，命中区域不小于 TouchMinSize。
5. WHEN 用户对 HornButton 执行短按（按下到抬起间隔 < 250 ms），THE HornButton SHALL 发送一次 `cmd.audio` 短鸣指令。
6. WHEN 用户对 HornButton 执行长按（按下持续 ≥ 250 ms），THE HornButton SHALL 在越过 250ms 阈值时发送 `hornStart` 指令，并在抬起时发送 `hornStop` 指令。
7. IF 用户在一次按压周期内同时满足短按与长按的潜在触发，THEN THE HornButton SHALL 仅触发其中一种语义（长按优先）。

### Requirement 9 — 右侧悬浮操作组

**User Story:** 作为驾驶员，我希望快速打开灯光、音响与模式，以便按场景切换。

#### Acceptance Criteria

1. THE FloatingActionGroup SHALL 在屏幕右侧中部以竖排形式渲染 3 个按钮，分别对应灯光、音响、模式切换入口。
2. THE FloatingActionGroup 的每个按钮 SHALL 具备 ≥ TouchMinSize 的命中区域。
3. WHEN 用户点击灯光按钮，THE FloatingActionGroup SHALL 切换 LightPopover 的显隐。
4. WHEN 用户点击音响按钮，THE FloatingActionGroup SHALL 切换 AudioPopover 的显隐。
5. WHEN 用户点击模式按钮，THE FloatingActionGroup SHALL 切换 ModeSwitch 的显隐或直接在该按钮内切换模式（具体样式由 design 阶段确定）。
6. THE FloatingActionGroup SHALL 保证在任意时刻最多只打开一个弹框。

### Requirement 10 — 灯光弹框

**User Story:** 作为驾驶员，我希望在一个面板里控制大灯和灯带，以便节省空间。

#### Acceptance Criteria

1. THE LightPopover SHALL 包含大灯开关、亮度滑块（0–100）、灯带模式选择（复用后端已支持的模式集合）。
2. WHEN 用户调整大灯开关或亮度滑块，THE LightPopover SHALL 通过现有 `cmd.light` 指令发送，payload 字段沿用现有后端约定。
3. WHEN 用户切换灯带模式，THE LightPopover SHALL 通过现有 `cmd.light` 指令发送，并使用 `CarStore.lighting` 作为数据源显示当前模式。
4. WHEN 指针在 LightPopover 矩形之外按下（`pointerdown`），THE LightPopover SHALL 关闭自身。
5. IF 指针在 LightPopover 矩形之内按下，THEN THE LightPopover SHALL 保持打开状态。

### Requirement 11 — 音响弹框

**User Story:** 作为驾驶员，我希望在一个面板里控制音量、麦克风与 TTS，以便语音互动。

#### Acceptance Criteria

1. THE AudioPopover SHALL 包含音量滑块（0–100）、麦克风开关、TTS 文本输入与发送按钮。
2. WHEN 用户调整音量，THE AudioPopover SHALL 通过现有 `cmd.audio` 指令发送 `volume` action。
3. WHEN 用户切换麦克风开关，THE AudioPopover SHALL 通过现有 `cmd.audio` 指令发送麦克风 action。
4. WHEN 用户提交 TTS 文本，THE AudioPopover SHALL 通过现有 `cmd.audio` 指令发送 `tts` action，payload 字段沿用现有后端约定。
5. WHEN 指针在 AudioPopover 矩形之外按下，THE AudioPopover SHALL 关闭自身。
6. IF 指针在 AudioPopover 矩形之内按下，THEN THE AudioPopover SHALL 保持打开状态。

### Requirement 12 — 模式切换

**User Story:** 作为驾驶员，我希望在「手动」与「智能」之间一键切换，以便在遥控与自动之间转换。

#### Acceptance Criteria

1. THE ModeSwitch SHALL 对外呈现两档：`手动`、`智能`。
2. WHEN 用户选择 `手动`，THE ModeSwitch SHALL 发送 `cmd.mode`，payload 为 `{ "mode": "manual" }`。
3. WHEN 用户选择 `智能`，THE ModeSwitch SHALL 发送 `cmd.mode`，payload 的 `mode` 字段对应后端非手动模式（具体值如 `track` 由 design 阶段确认，但必须从现有后端已支持的枚举中选择）。
4. THE ModeSwitch SHALL 以 `CarStore.mode` 为唯一视觉数据源来回显当前模式。
5. WHEN 后端广播 `event.mode_changed` 并导致 `CarStore.mode` 变化，THE ModeSwitch SHALL 在 ≤ 200 ms 内更新视觉状态。

### Requirement 13 — 电量视觉映射

**User Story:** 作为驾驶员，我希望电量状态通过颜色和文字一致表达，并在危险时得到强提醒，以避免断电。

#### Acceptance Criteria

1. THE BatteryIndicator SHALL 以 `CarStore.sensors.battery_level` 为唯一数据源，且前端不引入任何电压数值阈值。
2. WHEN `battery_level = "ok"`，THE BatteryIndicator SHALL 显示文字「良好」并使用绿色视觉档位。
3. WHEN `battery_level = "low"`，THE BatteryIndicator SHALL 显示文字「偏低」并使用黄色视觉档位。
4. WHEN `battery_level = "critical"`，THE BatteryIndicator SHALL 显示文字「危险」，使用红色视觉档位，并以 800 ± 50 ms 为周期进行红色闪烁动画。
5. WHEN `battery_level = "unknown"`，THE BatteryIndicator SHALL 显示文字「未知」并使用灰色视觉档位。
6. THE BatteryIndicator SHALL 保证「档位文字」与「档位颜色」两者为 `battery_level` 的确定性函数（相同输入产出相同输出）。

### Requirement 14 — 底部数据条

**User Story:** 作为驾驶员，我希望能扫一眼看到速度与前后距离等实时数值，以便微调控制。

#### Acceptance Criteria

1. THE DataBar SHALL 固定在屏幕底部并横跨全宽。
2. THE DataBar SHALL 展示以下字段：`CarStore.motion.speed`、`CarStore.motion.direction`、`CarStore.sensors.front_distance`、`CarStore.sensors.rear_distance`、`CarStore.sensors.cpu_temp`、`CarStore.motion.nitro_active`。
3. WHEN 对应字段在 CarStore 中为 `null` 或 `undefined`，THE DataBar SHALL 显示占位符 `--`。
4. THE DataBar SHALL 在对应字段变化后 ≤ 200 ms 内更新视图。

### Requirement 15 — 赛博朋克视觉风格

**User Story:** 作为产品设计者，我希望面板具备赛博朋克质感，以形成辨识度。

#### Acceptance Criteria

1. THE CyberpunkPanel SHALL 至少使用以下 CSS 能力中的每一项一次：`box-shadow`（霓虹描边）、`backdrop-filter`（毛玻璃）、`animation`（呼吸或扫描线）、`mix-blend-mode`（图层混合）。
2. THE CyberpunkPanel SHALL 使用 CSS 渐变与 SVG 作为视觉装饰，且不引用任何位图素材文件。
3. THE CyberpunkPanel SHALL 保证所有装饰动画在 BaselineViewport 下的单帧合成耗时不阻塞主线程超过 16 ms（目标 60 FPS）。

### Requirement 16 — 图片素材占位与登记

**User Story:** 作为协作设计师，我希望清楚知道未来需要哪些位图素材及其规格，以便后续补齐。

#### Acceptance Criteria

1. THE CyberpunkPanel SHALL 在 `frontend/src/assets/cyberpunk/README.md` 登记所有计划使用的位图素材的名称、尺寸、格式、用途与占位策略。
2. WHERE 某个素材尚未提供，THE CyberpunkPanel SHALL 使用 CSS 渐变或内联 SVG 作为占位。
3. THE CyberpunkPanel SHALL 不在本特性的代码中引用任何位图文件。

### Requirement 17 — 后端契约零改动

**User Story:** 作为后端工程师，我希望前端改版不触碰任何后端文件，以保持协议与驱动的稳定性。

#### Acceptance Criteria

1. THE CyberpunkPanel SHALL 仅通过现有 `CarStore` 与现有 WebSocket envelope（`cmd.*` / `tel.*` / `event.*`）与后端交互。
2. THE CyberpunkPanel SHALL 不修改 `app/` 目录下的任何文件。
3. THE CyberpunkPanel SHALL 不引入新的 `cmd.*` 类型或 `tel.*` 类型。
4. IF 后端下发字段为 `null` / `undefined`，THEN THE CyberpunkPanel SHALL 使用占位符显示而不崩溃。

## Correctness Properties (PBT 候选)

以下属性面向后续 Property-Based Testing，每条都可由纯函数或可隔离的组件逻辑覆盖：

- **P1 摇杆归一化（对应 R6、R7）**：对任意指针偏移 `(dx, dy) ∈ ℝ²` 与外圆半径 `R > 0`，`clampToUnitDisk(dx/R, dy/R)` 的结果向量 `(u, v)` 必须满足 `u² + v² ≤ 1 + 1e-6`，且当 `|(dx, dy)| ≤ R` 时有 `(u, v) = (dx/R, dy/R)`（线性区等价）。
- **P2 摇杆释放回中（对应 R6.4、R7.4）**：在任意拖动序列之后触发释放事件，组件对外发出的最后一条运动/云台指令 payload 必须等于 `(0, 0)`。
- **P3 电量分档纯函数（对应 R13）**：映射 `mapBatteryLevel(level) → { text, colorClass, blink }` 必须是确定性函数，其值域在 `{良好, 偏低, 危险, 未知}` 与对应固定颜色/闪烁 flag 之间；对任意不在 `{ok, low, critical, unknown}` 之外的输入必须回落到 `未知`。
- **P4 BRAKE 100ms 循环（对应 R8.2、R8.3）**：对任意按压持续时长 `T`（毫秒），BrakeButton 在按压期间发送的 `cmd.brake` 次数 `N` 必须满足 `floor(T/100) ≤ N ≤ floor(T/100) + 2`（首帧 + 允许 1 帧抖动）；释放后的 100 ms 内不得再发出 `cmd.brake`。
- **P5 HORN 短/长按分支（对应 R8.5–R8.7）**：对任意按压时长 `T`，当 `T < 250 ms` 时 HornButton 仅发送一次「短鸣」指令；当 `T ≥ 250 ms` 时仅发送一次 `hornStart` 与一次 `hornStop`，两者不共存。
- **P6 弹框外部点击关闭（对应 R10.4–R10.5、R11.5–R11.6）**：对任意点击坐标 `(x, y)` 与弹框矩形 `R`，若 `(x, y) ∉ R` 则弹框关闭；若 `(x, y) ∈ R` 则弹框保持打开。该属性对 LightPopover 与 AudioPopover 同时成立。
- **P7 运动保活（对应 R6.3、R7.3）**：在用户按住摇杆的任意窗口 `[t0, t0 + T]` 内，发送的 `cmd.motion` / `cmd.gimbal` 次数 `N` 满足 `floor(T/120) ≤ N ≤ floor(T/80) + 1`（允许 100 ± 20 ms 抖动）。
- **P8 倒车 PiP 触发（对应 R5.2、R5.3）**：对任意 `CarStore.motion.vy` 序列，ReversePiP 的放大态 `enlarged(t)` 必须等于 `vy(t) < 0` 的布尔值（忽略过渡动画的中间状态）。
