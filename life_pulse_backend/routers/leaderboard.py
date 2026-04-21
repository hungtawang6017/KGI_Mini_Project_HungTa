"""
routers/leaderboard.py — 相對排行榜 API

端點：GET /api/leaderboard/relative/{agent_id}
職責：回傳以當前業務員為中心的「相對排名視圖」，隱匿所有他人的真實身分。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from crud import get_relative_leaderboard, get_branch_leaderboard
from schemas import RelativeLeaderboardResponse

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard — 排行榜"])


@router.get(
    "/relative/{agent_id}",
    response_model=RelativeLeaderboardResponse,
    summary="取得相對排行榜",
    description=(
        "以指定業務員為中心，回傳其前後 2 名的本週排名資訊。"
        "所有他人的 agent_id 均被替換為不可逆的匿名代號，保護員工隱私。"
        "當前使用者顯示為 'YOU'。"
    ),
)
def relative_leaderboard(
    agent_id: str,
    db: Session = Depends(get_db),
):
    result = get_relative_leaderboard(db=db, agent_id=agent_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"業務員 {agent_id} 本週尚無學習紀錄，請先完成至少一次學習衝刺。",
        )

    return RelativeLeaderboardResponse(**result)

@router.get(
    "/branch",
    summary="取得分行對戰排行榜",
    description="回傳本週各分行的總分排行。可選傳入 agent_id，回傳中將包含 my_branch 欄位以供前端高亮使用者所屬分行。",
)
def branch_leaderboard(agent_id: str = None, db: Session = Depends(get_db)):
    result = get_branch_leaderboard(db=db, agent_id=agent_id)
    return result
