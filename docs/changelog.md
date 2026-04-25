# 变更日志

> 倒序追加，最新条目在最上方。  
> 每天下班前 3-5 分钟填写。超过 4 周的条目移至 `docs/archive/`。  
> 格式：日期 / 完成 / 问题 / 明天计划

---

## 模板（复制这段开始写）

```
## YYYY-MM-DD

**完成：**
- 

**问题：**
- 

**明天计划：**
- 
```

---



## 2026-04-25

**完成：**

- ADS1115 硬件接线完成：I2C1_M4（物理脚 3/5），20KΩ+10KΩ 分压电路，`i2cdetect -y 1` 确认 `0x48`
- 裸验证脚本在板端实测：连续 5 次读数 7.93-7.94V，波动 ±0.01V，非常稳定
- ADS1115 ADC 驱动实现：`app/drivers/adc/`（Real + Mock 双实现，零第三方依赖，原始 I2C 操作）
- Sensing 子系统实现：`app/subsystems/sensing.py`（电池电压/电量百分比/等级 + CPU 温度）
- Telemetry 改造：`tel.sensors` 从 mock 随机值切换为真实 ADS1115 读数 + sysfs CPU 温度
- `config.py` 新增 ADS1115 / 电池参数（I2C 总线、地址、FSR、分压比、电压阈值）
- `main.py` 组装 sensing 子系统（init + cleanup 生命周期）
- 现有 8 个测试全部通过，无回归

**问题：**

- 分压比使用理论值 3.0，尚未用万用表校准实际偏差
- `tel.sensors` 中 `wifi_rssi`、`ws_latency_ms`、`cpu_usage` 字段暂时移除（原为 mock 值），前端如有依赖需确认

**明天计划：**

- [ ] 万用表校准分压比，如有偏差在 config 中修正
- [ ] 部署到板端跑全链路端对端测试
- [ ] 确认前端 `tel.sensors` 字段变更是否需要适配
- [ ] Phase 2.pre 收尾，准备进入 Phase 3（FPV 摄像头）

## 2026-04-23（初始化）

**完成：**

- Phase 2.1（电机控制核心）✅ 已完成，三层抽象验证通过
- Phase 2.2（FastAPI + WebSocket + Vue 控制面板）✅ 全栈运行，端对端联调完成
- ADS1115 与 sensing 方案已定，代码待落地
- WebSocket 遥测循环已实现（`tel.motion` + mock `tel.sensors`）
- 文档架构初始化（CLAUDE.md + docs/ 全套）
- 补齐 `cmd.brake` 后端分发：立即制动、返回 `event.ack`，并加入短保护窗口忽略旧运动指令
- 前端刹车按钮接入控制链路，触发时重置摇杆/键盘输入
- 新增 dispatcher 测试，覆盖刹车 ack 与旧运动指令抑制

**问题：**

- ADS1115 实体接线尚未完成，裸验证脚本和真板读数验证待补

**明天计划：**

- [x] 接 LM2596S，调压至 5.0V，用万用表验证
- [ ] 接 ADS1115（I2C1_M4，物理脚 3/5）+ 分压电路（20KΩ+10KΩ）
- [ ] 编写并运行 ADS1115 裸验证脚本，确认 I2C 通信正常，电压读数合理
- [ ] 通过后做全链路端对端测试，Phase 2.pre 收尾
