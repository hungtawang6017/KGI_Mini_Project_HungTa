"""
routers/dev.py — 開發測試專用 API
⚠️  僅供開發/測試環境使用，上線前應移除或以環境變數控管
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from crud import award_points_and_update_streak, run_daily_settlement, _get_epoch_week, perform_weekly_settlement
from models import PointLedger, AgentStreaks, LeaderboardStandings
from schemas import CompleteSessionResponse, StreakStatus, SettlementResult
from datetime import date, timedelta
import os
from seed_data import seed as run_seed_logic

router = APIRouter(prefix="/api/dev", tags=["Dev — 開發測試（上線前移除）"])

BONUS_EVENTS = {
    "quiz_perfect":    5,
    "bio_rhythm_bonus": 2,
    "streak_bonus":    3,
}


@router.post("/award-bonus/{agent_id}", summary="發放加成積分（測試用）")
def award_bonus(agent_id: str, event_type: str = "quiz_perfect", db: Session = Depends(get_db)):
    """
    發放指定類型的加成積分。
    - quiz_perfect    → +5（滿分測驗）
    - bio_rhythm_bonus → +2（生理節律加成）
    - streak_bonus    → +3（連勝獎勵）
    """
    if event_type not in BONUS_EVENTS:
        raise HTTPException(400, f"event_type 必須是: {list(BONUS_EVENTS.keys())}")

    pts = BONUS_EVENTS[event_type]
    try:
        entry = PointLedger(agent_id=agent_id, event_type=event_type, points_awarded=pts)
        db.add(entry)

        # 更新排行榜快取
        epoch_week = _get_epoch_week()
        standing = db.query(LeaderboardStandings).filter(
            LeaderboardStandings.agent_id == agent_id,
            LeaderboardStandings.epoch_week_number == epoch_week,
        ).first()
        if standing:
            standing.weekly_points_total = (standing.weekly_points_total or 0) + pts

        db.commit()
        return {"success": True, "event_type": event_type, "points_awarded": pts}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


@router.post("/simulate-settlement", summary="模擬昨日結算（測試用）")
def simulate_settlement(db: Session = Depends(get_db)):
    """手動觸發昨日連勝結算（等同 APScheduler 每日 00:01 的行為）。"""
    try:
        result = run_daily_settlement(db)
        db.commit()
        return {"success": True, **result}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
 
 
@router.post("/weekly-settlement", summary="模擬每週日結算（測試用）")
def simulate_weekly_settlement(db: Session = Depends(get_db)):
    """手動觸發每週日積分歸零與歷史存檔。"""
    try:
        perform_weekly_settlement(db)
        return {"success": True, "message": "已模擬每週日結算，本週積分已存入歷史並歸零。"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


@router.post("/increase-streak/{agent_id}", summary="增加連續學習天數（測試用）")
def increase_streak(agent_id: str, db: Session = Depends(get_db)):
    """
    手動將連勝天數 +1。
    - 規則：每達 3 天自動獲得 1 面防護罩。
    - 同步更新歷史最長連勝紀錄。
    """
    from crud import SHIELD_STREAK_THRESHOLD
    try:
        streak = db.query(AgentStreaks).filter(AgentStreaks.agent_id == agent_id).first()
        if not streak:
            streak = AgentStreaks(agent_id=agent_id, current_streak_days=0, active_shields_count=0)
            db.add(streak)
        
        streak.current_streak_days = (streak.current_streak_days or 0) + 1
        streak.last_study_date = date.today()

        # 更新歷史最長紀錄
        if streak.current_streak_days > (streak.longest_historical_streak or 0):
            streak.longest_historical_streak = streak.current_streak_days

        shield_awarded = False
        # 只要累計滿 3 天就發放防護罩（測試面板不設上限，方便測試）
        streak.streak_shield_counter = (streak.streak_shield_counter or 0) + 1
        if streak.streak_shield_counter >= SHIELD_STREAK_THRESHOLD:
            streak.active_shields_count = (streak.active_shields_count or 0) + 1
            streak.streak_shield_counter = 0 # 重置計數器
            shield_awarded = True

        db.commit()
        return {
            "success": True, 
            "current_streak_days": streak.current_streak_days,
            "longest_historical_streak": streak.longest_historical_streak,
            "active_shields_count": streak.active_shields_count,
            "shield_awarded": shield_awarded
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


@router.post("/break-streak/{agent_id}", summary="中斷連續學習（測試用）")
def break_streak(agent_id: str, db: Session = Depends(get_db)):
    """
    模擬「昨天沒上課」的情境。
    - 若有防護罩：扣除 1 面，連勝天數維持。
    - 若無防護罩：連勝天數歸零。
    """
    try:
        streak = db.query(AgentStreaks).filter(AgentStreaks.agent_id == agent_id).first()
        if not streak:
            raise HTTPException(404, "找不到此業務員的連勝紀錄")

        shield_consumed = False
        if (streak.active_shields_count or 0) > 0:
            streak.active_shields_count -= 1
            shield_consumed = True
        else:
            streak.current_streak_days = 0
            streak.streak_shield_counter = 0

        # 將最後學習日設為前天，模擬昨日中斷
        streak.last_study_date = date.today() - timedelta(days=2)

        db.commit()
        return {
            "success": True, 
            "current_streak_days": streak.current_streak_days,
            "active_shields_count": streak.active_shields_count,
            "shield_consumed": shield_consumed
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


@router.post("/reset-agent/{agent_id}", summary="重置指定業務員資料（測試用）")
def reset_agent(agent_id: str, db: Session = Depends(get_db)):
    """清除指定 agent 的所有 streak 資料與本週積分（保留 PointLedger 歷史）。"""
    try:
        streak = db.query(AgentStreaks).filter(AgentStreaks.agent_id == agent_id).first()
        if streak:
            streak.current_streak_days = 0
            streak.active_shields_count = 0
            streak.last_study_date = None

        epoch_week = _get_epoch_week()
        standing = db.query(LeaderboardStandings).filter(
            LeaderboardStandings.agent_id == agent_id,
            LeaderboardStandings.epoch_week_number == epoch_week,
        ).first()
        if standing:
            standing.weekly_points_total = 0

        db.commit()
        return {"success": True, "message": f"{agent_id} 的資料已重置"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))


@router.post("/seed", summary="植入測試資料")
def run_seed():
    """直接呼叫 seed 邏輯，避免進程啟動開銷。"""
    try:
        run_seed_logic()
        return {"success": True, "message": "測試資料已重新植入"}
    except Exception as e:
        raise HTTPException(500, f"Seed 失敗: {str(e)}")


@router.get("/agents", summary="列出所有業務員狀態（測試用）")
def list_agents(db: Session = Depends(get_db)):
    """回傳所有業務員的本週積分與連勝狀態，用於測試驗證。"""
    epoch_week = _get_epoch_week()
    standings = db.query(LeaderboardStandings).filter(
        LeaderboardStandings.epoch_week_number == epoch_week
    ).all()
    streaks_map = {s.agent_id: s for s in db.query(AgentStreaks).all()}

    result = []
    for s in sorted(standings, key=lambda x: x.weekly_points_total, reverse=True):
        streak = streaks_map.get(s.agent_id)
        result.append({
            "agent_id": s.agent_id,
            "branch_id": s.branch_id,
            "weekly_points": s.weekly_points_total,
            "streak_days": streak.current_streak_days if streak else 0,
            "shields": streak.active_shields_count if streak else 0,
        })
    return result
