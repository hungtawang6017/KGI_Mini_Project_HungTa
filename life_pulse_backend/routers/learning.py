"""
routers/learning.py — 學習完成 API

端點：POST /api/learning/complete-session
職責：業務員完成 7 分鐘微學習後觸發，執行規則 1（積分派發）與規則 2（防護罩發放）。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from crud import award_points_and_update_streak, get_user_status, get_user_history
from schemas import CompleteSessionRequest, CompleteSessionResponse, StreakStatus, WeeklyHistoryEntry

router = APIRouter(prefix="/api/learning", tags=["Learning — 學習引擎"])


@router.post(
    "/complete-session",
    response_model=CompleteSessionResponse,
    summary="完成學習衝刺（規則 1 + 2）",
    description="業務員完成一次 7 分鐘微學習後呼叫。系統寫入 +10 積分至 PointLedger，並判定是否觸發連勝防護罩。",
)
def complete_session(
    request: CompleteSessionRequest,
    db: Session = Depends(get_db),
):
    """
    金融級事務保護：
    - 成功 → commit() 確認所有寫入
    - 任何異常 → rollback() 回滾，確保 PointLedger 與 AgentStreaks 的一致性
    """
    try:
        ledger_entries, streak, shield_awarded = award_points_and_update_streak(
            db=db,
            agent_id=request.agent_id,
            event_type=request.event_type,
            is_quiz_perfect=request.is_quiz_perfect
        )
        db.commit()
        # Refresh the first entry for transaction ID reference (or return total points)
        db.refresh(ledger_entries[0])
        db.refresh(streak)

        total_points = sum(entry.points_awarded for entry in ledger_entries)

        return CompleteSessionResponse(
            success=True,
            transaction_id=ledger_entries[0].transaction_id,
            points_awarded=total_points,
            streak=StreakStatus(
                current_streak_days=streak.current_streak_days,
                longest_historical_streak=streak.longest_historical_streak,
                active_shields_count=streak.active_shields_count,
                has_studied_today=True,
                shield_awarded=shield_awarded,
            ),
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"學習記錄寫入失敗，交易已回滾。原因：{str(e)}",
        )

@router.get(
    "/status/{agent_id}",
    response_model=StreakStatus,
    summary="取得業務員當前狀態",
)
def get_status(agent_id: str, db: Session = Depends(get_db)):
    status_data = get_user_status(db, agent_id)
    return StreakStatus(
        current_streak_days=status_data["current_streak_days"],
        longest_historical_streak=status_data.get("longest_historical_streak", 0),
        active_shields_count=status_data["active_shields_count"],
        streak_shield_counter=status_data["streak_shield_counter"],
        has_studied_today=status_data["has_studied_today"],
        shield_awarded=False
    )

@router.get(
    "/history/{agent_id}",
    response_model=List[WeeklyHistoryEntry],
    summary="取得個人歷史週積分紀錄",
)
def list_history(agent_id: str, db: Session = Depends(get_db)):
    """回傳該業務員過去每一週結算時的總積分紀錄。"""
    history = get_user_history(db, agent_id)
    return history
