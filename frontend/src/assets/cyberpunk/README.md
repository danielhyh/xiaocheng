# Cyberpunk Control Panel — 位图素材登记表

> 本特性所有视觉首轮使用纯 CSS 渐变 / SVG / 占位块。
> 本文件登记**后续**可替换为位图的槽位与规格,便于设计师按规格出图。
>
> **约束 (R16)**: 本特性代码**不引用**任何位图文件。
> 所有占位槽位都有对应的 CSS 渐变 / SVG 兜底, 可以先跑起来再逐步替换。

## 命名约定

- 统一放置于 `frontend/src/assets/cyberpunk/` 下, 子目录按区域划分
- 命名: `{slot}-{variant}@{scale}x.{ext}`, 例如 `hud-bar-bg@2x.webp`
- 主力格式 **WebP** (有损 Q85, 带透明通道优先) + **PNG** 兜底
- 每张图需同时出一份 1x / 2x; PC 档 (视口 ≥ 900px) 额外出 3x

## 待补位图清单

| 槽位 ID | 用途 | 目标视口 (基线) | 规格 (1x) | 格式 | 占位策略 (当前) | 建议底图描述 |
|---|---|---|---|---|---|---|
| `fpv-bg-ambient` | FPVStage 离线/无信号占位 | 整屏 812×375 | 1280×720 | WebP/PNG | `radial-gradient` + CSS scan line | 赛博朋克雨夜街道俯视, 暗紫 + 霓虹蓝点 |
| `panel-frame-border` | 整体边框装饰 (四边 + 四角) | 整屏 | 1672×941 (源) | PNG (透明底) | PNG 覆盖 + CSS 网格兜底 | 赛博朋克 HUD 合成外框, 透明底, 直接铺满视口 (已接入 `PanelFrame.vue`) |
| `panel-frame-corner-tl` | 左上角装饰切角 HUD | 顶部装饰 | 220×140 | SVG / WebP | 纯 SVG 描边 | 钛合金切角 + 微发光电路板纹理 |
| `panel-frame-corner-tr` | 右上角装饰切角 HUD | 同上 | 220×140 | SVG / WebP | 纯 SVG 描边 | 对称版 |
| `panel-frame-corner-bl` | 左下角装饰切角 | 同上 | 220×140 | SVG / WebP | 纯 SVG 描边 | 同上 |
| `panel-frame-corner-br` | 右下角装饰切角 | 同上 | 220×140 | SVG / WebP | 纯 SVG 描边 | 同上 |
| `hud-bar-bg` | 顶部 HUDBar 背景 | 宽度 812, 高 44 | 1624×88 | WebP | CSS gradient + 磨砂 | 工业金属条 + 微噪点 + 下缘霓虹线 |
| `hud-bracket-left` | HUD 左侧模式装饰挂件 | 44×88 | 88×176 | SVG | 纯 SVG | 棱角切割 + 指示灯孔 |
| `hud-bracket-right` | HUD 右侧状态装饰挂件 | 44×88 | 88×176 | SVG | 纯 SVG | 对称 |
| `joy-ring-move` | MoveJoystick 外圆底座 | 120×120 | 240×240 | WebP/PNG | CSS radial + SVG 箭头 | 金属环 + 青色呼吸灯带, 中心透光 |
| `joy-thumb-move` | MoveJoystick 拇指 | 44×44 | 88×88 | WebP/PNG | CSS 半透 + 发光 | 磨砂玻璃拇指 + 霓虹边缘 |
| `joy-ring-gimbal` | GimbalJoystick 外圆 | 120×120 | 240×240 | WebP/PNG | CSS radial + SVG | 金属环 + 绿色呼吸灯 + 相机图标 |
| `joy-thumb-gimbal` | GimbalJoystick 拇指 | 44×44 | 88×88 | WebP/PNG | CSS 半透 + 发光 | 绿色磨砂 + 中心十字 |
| `btn-brake` | BRAKE 按钮 | 72×72 | 144×144 | WebP/PNG | CSS radial + 发光环 | 红色立体按钮, 顶部高光, 侧面金属圈 |
| `btn-brake-pressed` | BRAKE 按下态 | 72×72 | 144×144 | WebP/PNG | :active 变换 | 同上, 压下 2px, 底部红光更亮 |
| `btn-horn` | HORN 按钮 | 62×62 | 124×124 | WebP/PNG | CSS radial + 发光环 | 青色立体按钮, 喇叭浮雕 |
| `btn-horn-loop` | HORN 长按态 | 62×62 | 124×124 | WebP/PNG | animate-pulse | 外圈呼吸, 喇叭周围发射波纹 |
| `fab-gimbal` | 右侧悬浮按钮 - 云台 | 44×44 | 88×88 | SVG / WebP | SVG | 绿色十字准心圆章 |
| `fab-light` | 右侧悬浮按钮 - 灯光 | 44×44 | 88×88 | SVG / WebP | SVG | 黄色灯泡圆章 |
| `fab-audio` | 右侧悬浮按钮 - 音响 | 44×44 | 88×88 | SVG / WebP | SVG | 青色扬声器圆章 |
| `popover-bg-light` | LightPopover 玻璃底板 | 260×260 | 520×520 | WebP | glass gradient | 深海蓝磨砂 + 左上霓虹折射光 |
| `popover-bg-audio` | AudioPopover 玻璃底板 | 260×220 | 520×440 | WebP | glass gradient | 同上, 稍偏紫 |
| `reverse-pip-frame` | ReversePiP 外框 | 按 vw% 动态 | 600×320 | WebP | SVG + CSS | 洋红切角外框 + REC 指示槽 |
| `reverse-pip-placeholder` | ReversePiP 无流占位 | 同上 | 600×320 | WebP | CSS 渐变 + SVG 假地平线 | 夜视风后视: 车尾轮廓 + 远处霓虹残影 |
| `data-bar-bg` | 底部 DataBar 背景 | 宽 812, 高 40 | 1624×80 | WebP | CSS gradient | 工业金属条 + 上缘霓虹线 + 栅格 |
| `orientation-phone` | OrientationGuard 手机图标 | 96×96 | 192×192 | SVG | 纯 SVG | 线性手机 + 箭头, 霓虹渐变描边 |
| `mode-switch-track` | ModeSwitch 轨道槽 | 180×32 | 360×64 | SVG / WebP | CSS pill | 青色 <-> 洋红渐变轨道 |
| `battery-icon-base` | BatteryIndicator 外壳 | 36×16 | 72×32 | SVG | 纯 SVG | 精细金属电池外壳 |
| `logo-xiaocheng` | 顶部品牌 LOGO (预留) | 60×20 | 120×40 | SVG / WebP | 暂缺 | "小橙 / XiaoCheng" 赛博风字标 |

## 可选背景素材 (营造氛围, 非必需)

| 槽位 ID | 用途 | 规格 | 备注 |
|---|---|---|---|
| `scene-rain-overlay` | 全屏雨点叠加层 | 1920×1080 PNG | 透明底, 叠加到 FPVStage |
| `noise-grain` | 全屏颗粒噪点 | 512×512 PNG (tileable) | 叠加到 PanelFrame, mix-blend-mode: overlay |
| `logo-glitch-mask` | LOGO/HUD glitch 掩膜 | 按需 | 极低优先级 |

## 交付格式建议

- 主图走 **WebP** (Q85), 文件大小控制在 ≤ 60KB/张 (1x); 2x ≤ 200KB
- 所有按钮 / 图标首选 **SVG** (零尺寸成本 + 可变色)
- 装饰类边框、背景走 WebP 点阵
- 发光 / 半透效果尽量保留在 CSS 层, 位图只出"底座", 不要烘焙发光

## 接入步骤 (出图后替换占位)

1. 将位图放入 `frontend/src/assets/cyberpunk/<category>/<slot>.webp`
2. 在对应组件的 CSS 中用 `background-image: url('@/assets/cyberpunk/...')` 覆盖占位渐变
3. 保留 CSS 渐变作为 fallback (放在 `background` 的末段)
4. 若使用 `<img>`, 确保 `alt` 非空 (无障碍)
