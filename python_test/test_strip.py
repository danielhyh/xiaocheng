"""
test_strip.py — WS2812B 灯带首次点灯测试（独立脚本，在小橙上跑）

用法（小橙上，已激活 venv）:
    source .venv/bin/activate
    pip install spidev          # 若未装
    python python_test/test_strip.py

依次显示: 红 → 绿 → 蓝 → 白 → 流水 → 熄灭。
若颜色顺序对、10 颗都亮、首颗不乱闪 → 直连 3.3V 信号 OK，无需 74AHCT125。
若首颗乱闪/颜色错乱 → 信号电平不足，加二极管降压或 74AHCT125（见 hardware-wiring.md Phase 8）。
"""

import time

import spidev

NUM_LEDS = 10
SPI_BUS = 0
SPI_DEV = 0          # /dev/spidev0.0
SPI_SPEED = 6_400_000
BRIGHTNESS = 60      # 0-255，首测调低，护眼也省电

# WS2812B '0'→0xC0(高2/8) '1'→0xF8(高5/8)，每 bit 用 1 个 SPI 字节
_BIT = (0xC0, 0xF8)


def encode_byte(b: int) -> list[int]:
    return [_BIT[(b >> (7 - i)) & 1] for i in range(8)]


def encode_pixels(pixels: list[tuple[int, int, int]]) -> list[int]:
    """pixels: [(r,g,b), ...] → SPI 字节流（WS2812B 是 GRB 顺序）"""
    out: list[int] = []
    s = BRIGHTNESS / 255
    for r, g, b in pixels:
        out += encode_byte(int(g * s))
        out += encode_byte(int(r * s))
        out += encode_byte(int(b * s))
    out += [0x00] * 64  # reset: >50μs 低电平
    return out


def main() -> None:
    spi = spidev.SpiDev()
    spi.open(SPI_BUS, SPI_DEV)
    spi.max_speed_hz = SPI_SPEED
    spi.mode = 0
    print(f"SPI 打开成功: /dev/spidev{SPI_BUS}.{SPI_DEV} @ {SPI_SPEED} Hz")

    def show(pixels: list[tuple[int, int, int]]) -> None:
        spi.writebytes2(encode_pixels(pixels))

    try:
        for name, color in [
            ("红", (255, 0, 0)),
            ("绿", (0, 255, 0)),
            ("蓝", (0, 0, 255)),
            ("白", (255, 255, 255)),
        ]:
            print(f"全部 {name}")
            show([color] * NUM_LEDS)
            time.sleep(1.2)

        print("流水（逐颗点亮）")
        for i in range(NUM_LEDS):
            px = [(0, 0, 0)] * NUM_LEDS
            px[i] = (0, 128, 255)
            show(px)
            time.sleep(0.15)

        print("熄灭")
        show([(0, 0, 0)] * NUM_LEDS)
    finally:
        spi.writebytes2(encode_pixels([(0, 0, 0)] * NUM_LEDS))
        spi.close()
        print("完成，SPI 已关闭")


if __name__ == "__main__":
    main()
