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
mode_manager = ModeManager()
dispatcher = Dispatcher(motion, mode_manager, audio=audio)
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

    # 注入依赖到 API 层
    ws_api.init(dispatcher, safety, telemetry)
    http_api.init(mode_manager)
    stream_api.init(vision)

    # 启动后台任务
    safety_task = asyncio.create_task(safety.run())

    # 播放开机音效
    asyncio.create_task(audio.play_startup())

    logger.info("小橙 就绪")
    yield

    # --- 关闭 ---
    logger.info("小橙 关闭中...")
    safety.stop()
    safety_task.cancel()
    audio.cleanup()
    vision.cleanup()
    sensing.cleanup()
    motion.cleanup()
    logger.info("小橙 已关闭")


# ============================================================
#  FastAPI 应用
# ============================================================
app = FastAPI(
    title="小橙 4WD",
    version="0.2.0",
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
