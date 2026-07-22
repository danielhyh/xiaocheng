"""
drivers/strip/real.py — WS2812B 灯带真实驱动

通过 SPI bitbang 方式驱动 WS2812B。
RK3588S 上 rpi_ws281x 不可用,改用 SPI MOSI 模拟单线协议。

WS2812B 时序 (800kHz):
  - 0 码: 高 0.4μs + 低 0.85μs
  - 1 码: 高 0.8μs + 低 0.45μs
  - Reset: 低 > 50μs

SPI 方案: SPI 时钟 6.4MHz,每个 WS2812B bit 用 8 个 SPI bit 表示:
  - 0 码 → 0b11000000 (0xC0)
  - 1 码 → 0b11111000 (0xF8)
  - 每个 LED 3 字节 (GRB) → 24 bit → 24 × 8 = 192 SPI bit = 24 SPI 字节

注意 (2026-06-24): 改用 spidev 模块而非裸文件写 (open(dev,"wb"))。
裸文件写不设置 SPI 时钟,依赖 overlay 默认速率,WS2812B 时序不可控;
spidev 模块显式锁 max_speed_hz=6.4MHz,首颗灯电平本就临界 (需 74AHCT125),
时序必须精确。见 hardware-wiring.md Phase 8。
"""

import logging

from app import config

logger = logging.getLogger(__name__)


def _parse_spidev(path: str) -> tuple[int, int]:
    """从 /dev/spidevB.D 解析出 (bus, device)"""
    name = path.rsplit("/", 1)[-1]            # spidev0.0
    bus_dev = name.replace("spidev", "")      # 0.0
    bus, dev = bus_dev.split(".")
    return int(bus), int(dev)

# SPI bitbang 编码表
_BIT_0 = 0xC0  # WS2812B '0': 高2/8 低6/8
_BIT_1 = 0xF8  # WS2812B '1': 高5/8 低3/8


class RealStripDriver:
    """
    WS2812B SPI bitbang 驱动。

    通过 SPI MOSI 引脚发送编码后的数据。
    需要 3.3V → 5V 电平转换 (74AHCT125)。
    """

    def __init__(self):
        self._num_leds = config.STRIP_NUM_LEDS
        self._spi_dev = config.STRIP_SPI_DEV
        self._spi_speed = config.STRIP_SPI_SPEED
        self._brightness = config.STRIP_DEFAULT_BRIGHTNESS
        self._buffer = [(0, 0, 0)] * self._num_leds  # (R, G, B)
        self._spi = None
        self._segments = config.STRIP_SEGMENTS

    @property
    def num_leds(self) -> int:
        return self._num_leds

    def init(self) -> None:
        try:
            import spidev
        except ImportError:
            logger.error(
                "spidev 模块未安装。请在 venv 中执行: pip install spidev"
            )
            raise

        bus, dev = _parse_spidev(self._spi_dev)
        try:
            self._spi = spidev.SpiDev()
            self._spi.open(bus, dev)
            self._spi.max_speed_hz = self._spi_speed  # 显式锁 6.4MHz,WS2812B 时序必须
            self._spi.mode = 0
            self.clear()
            logger.info(
                f"RealStripDriver 初始化完成 "
                f"(dev={self._spi_dev}, speed={self._spi_speed}, leds={self._num_leds})"
            )
        except FileNotFoundError:
            logger.error(
                f"SPI 设备 {self._spi_dev} 不存在 (bus={bus}, dev={dev})。"
                "请确认 SPI 已启用 (orangepiEnv.txt overlays 加 spi0-m2-cs0-spidev 后重启)"
            )
            raise

    def _encode_byte(self, byte: int) -> bytes:
        """将一个字节编码为 8 个 SPI 字节"""
        result = bytearray(8)
        for i in range(8):
            if byte & (0x80 >> i):
                result[i] = _BIT_1
            else:
                result[i] = _BIT_0
        return bytes(result)

    def _encode_pixel(self, r: int, g: int, b: int) -> bytes:
        """将 RGB 编码为 SPI 数据 (WS2812B 是 GRB 顺序)"""
        # 应用亮度
        scale = self._brightness / 255
        g2 = int(g * scale)
        r2 = int(r * scale)
        b2 = int(b * scale)
        return self._encode_byte(g2) + self._encode_byte(r2) + self._encode_byte(b2)

    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        if 0 <= index < self._num_leds:
            self._buffer[index] = (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b)),
            )

    def set_segment(self, segment: str, r: int, g: int, b: int) -> None:
        if segment == "all":
            for i in range(self._num_leds):
                self.set_pixel(i, r, g, b)
        elif segment in self._segments:
            start, end = self._segments[segment]
            for i in range(start, end + 1):
                self.set_pixel(i, r, g, b)
        else:
            logger.warning(f"未知灯带分段: {segment}")

    def show(self) -> None:
        if self._spi is None:
            return
        data = bytearray()
        for r, g, b in self._buffer:
            data.extend(self._encode_pixel(r, g, b))
        # 追加 reset 信号 (至少 50μs 低电平 = 40+ 个 0x00 字节 @6.4MHz)
        data.extend(b'\x00' * 64)
        try:
            # writebytes2 支持大缓冲区自动分块
            self._spi.writebytes2(list(data))
        except OSError as e:
            logger.error(f"SPI 写入失败: {e}")

    def clear(self) -> None:
        self._buffer = [(0, 0, 0)] * self._num_leds
        self.show()

    def set_brightness(self, brightness: int) -> None:
        self._brightness = max(0, min(255, brightness))
        logger.debug(f"灯带亮度: {self._brightness}/255")

    def cleanup(self) -> None:
        self.clear()
        if self._spi is not None:
            self._spi.close()
            self._spi = None
            logger.info("RealStripDriver 资源已释放")
