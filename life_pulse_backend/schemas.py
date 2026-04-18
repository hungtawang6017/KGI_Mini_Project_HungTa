"""
schemas.py — L.I.F.E. Pulse Pydantic 資料驗證層（Pydantic v2 相容版本）
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, List


# ============================
# 📥 Request Schemas
# ============================

class CompleteSessionRequest(BaseModel):
    agent_id: str = Field(..., description="業務員識別碼")
    event_type: str = Field(default="COURSE_COMPLETION", description="學習事件類型")
    is_quiz_perfect: bool = Field(default=False, description="測驗是否全對")


class DailySettlementRequest(BaseModel):
    settlement_date: Optional[date] = Field(
        default=None,
        description="結算日期（預設為昨日）。可手動指定用於補算或測試。",
    )


# ============================
# 📤 Response Schemas
# ============================

class StreakStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_streak_days: int
    longest_historical_streak: int
    active_shields_count: int
    streak_shield_counter: int = Field(default=0, description="盾牌進度計數器")
    has_studied_today: bool = Field(default=False, description="今天是否已完成學習")
    shield_awarded: bool = Field(description="本次學習是否觸發防護罩獎勵")


class CompleteSessionResponse(BaseModel):
    success: bool
    transaction_id: int
    points_awarded: int
    streak: StreakStatus


class LeaderboardEntry(BaseModel):
    """
    排行榜單一條目 — 隱私保護：
    - is_current_user=True → agent_code 顯示 "YOU"
    - is_current_user=False → agent_code 顯示匿名碼（不可逆）
    """
    rank_display: str
    agent_code: str
    weekly_points_total: int
    is_current_user: bool


class RelativeLeaderboardResponse(BaseModel):
    current_user_rank: int
    total_participants: int
    entries: List[LeaderboardEntry]


class WeeklyHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    epoch_week_number: str
    final_points: int
    settlement_date: date


class SettlementResult(BaseModel):
    success: bool
    settlement_date: date
    processed_count: int = Field(description="本次掃描的業務員總數")
    shields_consumed: int = Field(description="防護罩被消耗的人數")
    streaks_reset: int = Field(description="連勝被歸零的人數")
    streaks_preserved: int = Field(description="昨日有學習，連勝正常保留的人數")
