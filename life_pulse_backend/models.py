"""
models.py — L.I.F.E. Pulse ORM 資料模型

映射規則：
- 所有 __tablename__ 使用全小寫，對應 PostgreSQL 的大小寫敏感規則
- PointLedger 為 Append-only（不可變）事件帳本，絕對禁止 UPDATE / DELETE
- AgentStreaks 為狀態機，記錄連勝天數與防護罩庫存
- LeaderboardStandings 為每週快取視圖，支援週期性結算歸零
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, func
from database import Base


class PointLedger(Base):
    """
    積分帳本 — 不可變的事件溯源（Event Sourcing）核心表。

    ⚠️  APPEND-ONLY：此表僅允許 INSERT。
        任何 UPDATE 或 DELETE 操作都是架構違規，
        將破壞金融級可稽核性與積分重算能力。
    """
    __tablename__ = "pointledger"

    transaction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_id = Column(String, nullable=False, index=True, comment="業務員唯一識別碼")
    event_type = Column(String, nullable=False, comment="事件類型，如 COURSE_COMPLETION / QUIZ_PERFECT")
    points_awarded = Column(Integer, nullable=False, comment="本次派發積分（正整數）")
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="事件發生時間（伺服器端 UTC 時間自動填入）"
    )


class AgentStreaks(Base):
    """
    連勝狀態機 — 追蹤每位業務員的學習連勝與防護罩庫存。

    每位業務員對應唯一一筆紀錄（agent_id UNIQUE）。
    每日結算 CRON 會依據 last_study_date 判斷是否需扣除防護罩或歸零連勝。
    """
    __tablename__ = "agentstreaks"

    streak_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_id = Column(String, unique=True, nullable=False, index=True, comment="業務員唯一識別碼（每人唯一一筆）")
    current_streak_days = Column(Integer, default=0, nullable=False, comment="當前連續學習天數")
    longest_historical_streak = Column(Integer, default=0, nullable=False, comment="歷史最長連勝天數（不隨歸零消失）")
    active_shields_count = Column(Integer, default=0, nullable=False, comment="當前持有防護罩數量")
    streak_shield_counter = Column(Integer, default=0, nullable=False, comment="盾牌進度計數器（累計 3 天獲得一面）")
    last_study_date = Column(Date, nullable=True, index=True, comment="最後一次完成學習的日期（用於結算判定）")


class LeaderboardStandings(Base):
    """
    排行榜快取視圖 — 每週積分快照。

    使用 epoch_week_number（如 202618）作為週期標記，
    支援每週日晚間自動歸零並生成新週期的紀錄。
    """
    __tablename__ = "leaderboardstandings"

    standing_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_id = Column(String, nullable=False, index=True, comment="業務員唯一識別碼")
    branch_id = Column(String, nullable=True, comment="所屬分公司 ID（用於分公司對抗機制）")
    epoch_week_number = Column(String, nullable=False, index=True, comment="週期識別碼，格式 YYYYWW，如 202618")
    weekly_points_total = Column(Integer, default=0, nullable=False, index=True, comment="本週累計積分")

class WeeklyHistory(Base):
    """
    歷史週結算紀錄 — 儲存每位業務員過去每週的最終積分。
    """
    __tablename__ = "weeklyhistory"

    history_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_id = Column(String, nullable=False, index=True, comment="業務員唯一識別碼")
    epoch_week_number = Column(String, nullable=False, index=True, comment="週週期識別碼")
    final_points = Column(Integer, nullable=False, comment="結算時的總積分")
    settlement_date = Column(Date, server_default=func.now(), nullable=False, comment="結算日期")
