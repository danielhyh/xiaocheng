---
title: ADC 驱动
scope: ADS1115 I2C ADC 电池电压读取，含 Real/Mock，零第三方依赖
code: app/drivers/adc/
last_verified: 2026-06-25
decisions: [ADR-006, ADR-008]
---
# ADC 驱动

## 职责
原始 I2C 读取 ADS1115（挂 I2C1_M4，物理脚 3/5），换算分压后的电池电压。Real/Mock 同 Protocol。

## 关键实现 / 注意事项
- 安全必选项，不是可选遥测（见 ADR-006）：LM2596S 低压死区会导致 OPi 无声断电。
- 20KΩ + 10KΩ 分压，理论分压比 3.0，待万用表实测校准。
- 零第三方依赖，直接写 I2C 寄存器。
- `last_verified` 表示此前驱动/真板链路的验证日期；当前 2S2P + KF301 重接后，ADS1115 仍需重新 `i2cdetect`、比对万用表并复验 7.2V 告警。
