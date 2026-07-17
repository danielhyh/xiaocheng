"""
main.py — FastAPI 应用入口

组装所有层:
  驱动层 → 子系统层 → 业务层 → API 层

启动方式:
  PC 开发:  XIAOCHENG_MOCK=1 uvicorn app.main:app --reload
  开发板:   uvicorn app.main:app --host 0.0.0.0
"""

import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config
from app.subsystems.motion import MotionSubsystem
from app.subsystems.sensing import SensingSubsystem
from app.subsystems.vision import VisionSubsystem
from app.subsystems.audio import AudioSubsystem
from app.subsystems.lighting import LightingSubsystem
from app.subsystems.gimbal import GimbalSubsystem
from app.subsystems.obstacle import ObstacleSubsystem
from app.subsystems.nitro import NitroSubsystem
from app.business.mode_manager import ModeManager
from app.business.dispatcher import Dispatcher
from app.business.safety import SafetyWatchdog
from app.business.telemetry import TelemetryPublisher
from app.api import http as http_api
from app.api import websocket as ws_api
from app.api import stream as stream_api

# ============================================================
#  日志
# ============================================================
logging.basicConfig(
    level=logging.DEBUG if config.USE_MOCK else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================
#  全局组件
# ============================================================
motion = MotionSubsystem()
sensing = SensingSubsystem()
vision = VisionSubsystem()
audio = AudioSubsystem()
lighting = LightingSubsystem()
gimbal = GimbalSubsystem()
obstacle = ObstacleSubsystem()
nitro = NitroSubsystem()
mode_manager = ModeManager()
dispatcher = Dispatcher(
    motion, mode_manager,
    audio=audio, lighting=lighting,
    gimbal=gimbal, obstacle=obstacle, nitro=nitro,
)
safety = SafetyWatchdog(motion, mode_manager)
telemetry = TelemetryPublisher(motion, sensing)


# ============================================================
#  生命周期
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 启动 ---
    logger.info("=" * 50)
    logger.info(f"  小橙 启动中  |  Mock: {config.USE_MOCK}")
    logger.info("=" * 50)

    motion.init()
    sensing.init()
    vision.init()
    audio.init()
    lighting.init()
    gimbal.init()
    obstacle.init()

    # 注入依赖到 API 层
    ws_api.init(dispatcher, safety, telemetry)
    http_api.init(mode_manager)
    stream_api.init(vision)

    # 注入子系统到安全看门狗
    safety.set_audio(audio)
    safety.set_lighting(lighting)
    safety.set_gimbal(gimbal)
    safety.set_obstacle(obstacle)
    safety.set_nitro(nitro)

    # 注入子系统到遥测
    telemetry.set_obstacle(obstacle)
    telemetry.set_gimbal(gimbal)
    telemetry.set_nitro(nitro)

    # 注入子系统到氮气
    nitro.set_dependencies(motion=motion, lighting=lighting, audio=audio)

    # 启动后台任务
    safety_task = asyncio.create_task(safety.run())

    # 启动避障扫描
    obstacle.start_scanning()

    # 播放开机音效
    asyncio.create_task(audio.play_startup())

    logger.info("小橙 就绪")
    yield

    # --- 关闭 ---
    logger.info("小橙 关闭中...")
    safety.stop()
    safety_task.cancel()
    nitro.cleanup()
    obstacle.cleanup()
    gimbal.cleanup()
    audio.cleanup()
    lighting.cleanup()
    vision.cleanup()
    sensing.cleanup()
    motion.cleanup()
    logger.info("小橙 已关闭")


# ============================================================
#  FastAPI 应用
# ============================================================
app = FastAPI(
    title="小橙 4WD",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS (开发时前端跑在不同端口)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(http_api.router)
app.include_router(ws_api.router)
app.include_router(stream_api.router)

# 静态文件 (Vue dist) — 生产环境一体部署
# app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
