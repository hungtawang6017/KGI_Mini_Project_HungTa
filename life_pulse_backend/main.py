"""
main.py — L.I.F.E. Pulse FastAPI 應用主入口

職責：
1. 組裝所有路由（learning / leaderboard / streak）
2. 設定 CORS，允許本地前端（Vite port 5173）呼叫 API
3. 啟動 APScheduler 4.x：每日 00:01（台北時區）自動執行連勝結算
4. 優雅關閉：應用終止時同步停止排程器

APScheduler 4.x 說明（與 3.x 有重大 API 差異）：
- 使用 AsyncScheduler（非 BackgroundScheduler）
- 透過 FastAPI lifespan 管理生命週期
- 時區設定為 Asia/Taipei，確保換日線與台灣業務員作息一致
"""

import logging
from contextlib import asynccontextmanager

from apscheduler import AsyncScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crud import run_daily_settlement
from database import SessionLocal
from routers import learning, leaderboard, streak, dev

# =====================
# 📋 日誌設定
# =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("life_pulse")


# =====================
# ⏰ 每日結算任務函數
# =====================
async def scheduled_daily_settlement():
    """
    生產排程任務：每日 00:01 自動執行連勝結算。
    使用獨立的 DB Session（非 API 請求 Session），確保排程任務的連線安全。
    """
    logger.info("🔄 APScheduler: 每日連勝結算任務啟動...")
    db = SessionLocal()
    try:
        result = run_daily_settlement(db)
        db.commit()
        logger.info(
            f"✅ 結算完成 — 掃描: {result['processed_count']} 人 | "
            f"防護罩消耗: {result['shields_consumed']} | "
            f"連勝歸零: {result['streaks_reset']} | "
            f"正常保留: {result['streaks_preserved']}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 結算失敗，已回滾。原因: {e}")
    finally:
        db.close()


# =====================
# 🚀 FastAPI 應用生命週期（APScheduler 4.x 整合）
# =====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理應用啟動與關閉的資源生命週期（APScheduler 4.x async 模式）。"""
    async with AsyncScheduler() as scheduler:
        # 每日 00:01 台北時間自動執行連勝結算
        await scheduler.add_schedule(
            scheduled_daily_settlement,
            CronTrigger(hour=0, minute=1, timezone="Asia/Taipei"),
            id="daily_streak_settlement",
        )
        logger.info("⏰ APScheduler 4.x 啟動，每日 00:01 (Asia/Taipei) 自動執行連勝結算")
        yield
    logger.info("⏰ APScheduler 已優雅關閉")


# =====================
# 🌐 FastAPI App 建立
# =====================
app = FastAPI(
    title="L.I.F.E. Pulse API",
    description=(
        "## 遊戲化微學習系統 — 對抗遺忘曲線，攻佔零碎時間\n\n"
        "**核心遊戲化規則**：\n"
        "- 規則 1：完成課程 → `PointLedger` 寫入 +10 積分（Append-only）\n"
        "- 規則 2：連勝達 3 的倍數 → 自動發放防護罩\n"
        "- 規則 3：每日 00:01 結算；缺席者先扣盾，無盾則歸零連勝\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# =====================
# 🔒 CORS 設定
# =====================
# 生產環境應將 allow_origins 限縮至實際部署的前端網域
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite 開發伺服器（預設埠）
        "http://localhost:3000",   # 備用（如 CRA 或其他設定）
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# 📡 路由注冊
# =====================
app.include_router(learning.router)
app.include_router(leaderboard.router)
app.include_router(streak.router)
app.include_router(dev.router)


# =====================
# 🏠 根端點（健康檢查）
# =====================
@app.get("/", tags=["System"], summary="健康檢查")
def root():
    return {
        "service": "L.I.F.E. Pulse API",
        "status": "✅ Running",
        "docs": "/docs",
        "philosophy": "對抗遺忘曲線，攻佔零碎時間",
    }
