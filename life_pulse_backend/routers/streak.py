"""
routers/streak.py — 每日連勝結算 API

端點：POST /api/streak/daily-settlement
職責：每日連勝中斷判定引擎（規則 3）。

觸發模式：
  - 手動觸發：開發與測試時可直接呼叫此 API（支援指定 settlement_date）
  - 自動觸發：生產環境由 main.py 的 APScheduler 在每日 00:01 自動執行
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from crud import run_daily_settlement
from schemas import DailySettlementRequest, SettlementResult

router = APIRouter(prefix="/api/streak", tags=["Streak — 連勝引擎"])


@router.post(
    "/daily-settlement",
    response_model=SettlementResult,
    summary="每日連勝結算（規則 3）",
    description=(
        "掃描所有業務員的連勝狀態，對缺席者執行判定：\n\n"
        "- 有防護罩 → 扣除 1 面防護罩，連勝天數保留\n"
        "- 無防護罩 → current_streak_days 歸零（歷史最長連勝不受影響）\n\n"
        "不指定 settlement_date 時，預設為**昨日**。"
    ),
)
def daily_settlement(
    request: DailySettlementRequest = DailySettlementRequest(),
    db: Session = Depends(get_db),
):
    try:
        result = run_daily_settlement(db=db, settlement_date=request.settlement_date)
        db.commit()
        return SettlementResult(success=True, **result)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"每日結算失敗，交易已回滾。原因：{str(e)}",
        )
