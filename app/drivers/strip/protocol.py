"""
drivers/strip/protocol.py — WS2812B 灯带驱动接口定义

所有灯带驱动 (Real / Mock) 都必须实现这个 Protocol。
上层代码只依赖这个接口,不依赖具体实现。

灯带物理布局 (10 颗 LED,从左到右):
  [0] [1] [2]  |  [3] [4] [5] [6]  |  [7] [8] [9]
   左侧 (3颗)      尾灯中央 (4颗)      右侧 (3颗)

软件分段:
  - left:  索引 0-2  (左转向灯 / 左侧氛围)
  - tail:  索引 3-6  (尾灯 / 刹车灯 / 倒车灯)
  - right: 索引 7-9  (右转向灯 / 右侧氛围)
"""

from typing import Protocol


class StripDriverProtocol(Protocol):
    """WS2812B 灯带驱动接口"""

    @property
    def num_leds(self) -> int:
        """灯带像素数量。"""
        ...

    def init(self) -> None:
        """初始化灯带 (GPIO / SPI 配置)"""
        ...

    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        """
        设置单个像素颜色 (不立即刷新)。

        参数:
            index: 像素索引 (0 ~ num_leds-1)
            r, g, b: 颜色分量 (0-255)
        """
        ...

    def set_segment(self, segment: str, r: int, g: int, b: int) -> None:
        """
        设置整个分段颜色 (不立即刷新)。

        参数:
            segment: "left" / "tail" / "right" / "all"
            r, g, b: 颜色分量 (0-255)
        """
        ...

    def show(self) -> None:
        """将缓冲区数据刷新到灯带"""
        ...

    def clear(self) -> None:
        """全部熄灭并刷新"""
        ...

    def set_brightness(self, brightness: int) -> None:
        """
        设置全局亮度。

        参数:
            brightness: 0 (灭) ~ 255 (最亮)
        """
        ...

    def cleanup(self) -> None:
        """熄灭灯带,释放资源"""
        ...
