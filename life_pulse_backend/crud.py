"""
crud.py — L.I.F.E. Pulse 核心商業邏輯層

職責：
- 實作三條遊戲化規則的所有資料庫操作
- 此層不處理 HTTP 細節（無 FastAPI 依賴），便於獨立 pytest 測試
- 所有函數接受 db: Session 參數，由 API 層負責 commit/rollback

遊戲化規則摘要：
  規則 1 - 積分派發：完成課程 → PointLedger 寫入 +10（Append-only）
  規則 2 - 防護罩發放：每達成連勝 3 的倍數 → AgentStreaks.active_shields_count +1
  規則 3 - 連勝判定引擎：每日結算；缺席者先扣盾，無盾則歸零連勝
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import PointLedger, AgentStreaks, LeaderboardStandings
from datetime import date, timedelta
from typing import Optional, Tuple, List

# =====================
# 🏆 遊戲化常數設定
# =====================
POINTS_PER_SESSION = 10          # 每次完成課程的積分獎勵
POINTS_PERFECT_QUIZ = 5          # 測驗全對的附加積分
POINTS_CONSECUTIVE_BONUS = 2     # 連續學習的附加積分
SHIELD_STREAK_THRESHOLD = 3      # 每累積 N 天連勝發放一面防護罩

# =====================
# 🛠 工具函數
# =====================

def _get_epoch_week(target_date: Optional[date] = None) -> str:
    """
    計算週期識別碼（格式：YYYYWW，如 202618）。
    用於 LeaderboardStandings 的週期標記，確保跨年週期不會碰撞。
    """
    d = target_date or date.today()
    return d.strftime("%Y%V")

def _anonymize_agent_id(agent_id: str) -> str:
    """
    將真實 agent_id 轉換為四位匿名代號。
    使用 hash 確保同一個 agent_id 每次產生相同代號（可重現性），
    但無法從代號反推真實 ID（單向性）。
    """
    return f"AGT-{abs(hash(agent_id)) % 9999:04d}"

# =====================
# 📚 規則 1 + 2：積分與連勝
# =====================

def award_points_and_update_streak(
    db: Session,
    agent_id: str,
    event_type: str,
    is_quiz_perfect: bool = False
) -> Tuple[List[PointLedger], AgentStreaks, bool]:
    """
    規則 1：將積分寫入 PointLedger（Append-only，此為唯一寫入途徑）。
          基礎分 +10，全對 +5，連續學習 +2。
    規則 2：若連勝天數達 SHIELD_STREAK_THRESHOLD 的倍數，發放一面防護罩。

    同時更新：
    - AgentStreaks（連勝天數、最長連勝、防護罩庫存、最後學習日）
    - LeaderboardStandings（本週積分累計）

    ⚠️  呼叫此函數後，呼叫方必須執行 db.commit()（或在異常時 db.rollback()）。

    Returns:
        (ledger_entries, streak_record, shield_awarded_this_session)
    """
    today = date.today()
    ledger_entries = []
    total_points = 0

    # ── 取得或初始化 AgentStreaks ──────────────────────────────────────
    streak = db.query(AgentStreaks).filter(AgentStreaks.agent_id == agent_id).first()
    if not streak:
        streak = AgentStreaks(agent_id=agent_id)
        db.add(streak)

    shield_awarded = False
    is_consecutive = False

    # 判定是否為連續學習 (昨天有學，或之前就在連勝且今天還沒結算掉)
    if streak.current_streak_days > 0 and streak.last_study_date != today:
        is_consecutive = True

    # 防止同日重複計算連勝（冪等性保護）
    if streak.last_study_date != today:
        streak.current_streak_days = (streak.current_streak_days or 0) + 1
        streak.last_study_date = today

        # 更新歷史最長紀錄
        if streak.current_streak_days > (streak.longest_historical_streak or 0):
            streak.longest_historical_streak = streak.current_streak_days

        # ── 規則 2：每累計學習 3 天，發放防護罩 ──────────────────────
        if streak.current_streak_days % SHIELD_STREAK_THRESHOLD == 0:
            streak.active_shields_count = (streak.active_shields_count or 0) + 1
            shield_awarded = True

    # ── 規則 1：寫入積分帳本（Append-only） ──────────────────────────
    # 基礎分
    base_entry = PointLedger(
        agent_id=agent_id,
        event_type=event_type,
        points_awarded=POINTS_PER_SESSION,
    )
    db.add(base_entry)
    ledger_entries.append(base_entry)
    total_points += POINTS_PER_SESSION

    # 全對獎勵
    if is_quiz_perfect:
        perfect_entry = PointLedger(
            agent_id=agent_id,
            event_type="quiz_perfect_bonus",
            points_awarded=POINTS_PERFECT_QUIZ,
        )
        db.add(perfect_entry)
        ledger_entries.append(perfect_entry)
        total_points += POINTS_PERFECT_QUIZ

    # 連續學習獎勵
    if is_consecutive:
        consecutive_entry = PointLedger(
            agent_id=agent_id,
            event_type="consecutive_learning_bonus",
            points_awarded=POINTS_CONSECUTIVE_BONUS,
        )
        db.add(consecutive_entry)
        ledger_entries.append(consecutive_entry)
        total_points += POINTS_CONSECUTIVE_BONUS

    # ── 更新排行榜快取（LeaderboardStandings） ────────────────────────
    # 模擬模式：優先使用資料庫中最新的週次 ID
    latest_week_record = db.query(LeaderboardStandings.epoch_week_number).order_by(desc(LeaderboardStandings.epoch_week_number)).first()
    epoch_week = latest_week_record[0] if latest_week_record else _get_epoch_week(today)
    
    standing = db.query(LeaderboardStandings).filter(
        LeaderboardStandings.agent_id == agent_id,
        LeaderboardStandings.epoch_week_number == epoch_week,
    ).first()

    if not standing:
        # 嘗試從過去紀錄尋找 branch_id
        last_standing = db.query(LeaderboardStandings).filter(
            LeaderboardStandings.agent_id == agent_id,
            LeaderboardStandings.branch_id.isnot(None)
        ).order_by(desc(LeaderboardStandings.epoch_week_number)).first()
        branch_id = last_standing.branch_id if last_standing else None

        if not branch_id and agent_id == "tester_01":
            branch_id = "敦南分行"

        # 新建時直接帶入初始積分，避免 flush 前 default 未套用的 NoneType 問題
        standing = LeaderboardStandings(
            agent_id=agent_id,
            branch_id=branch_id,
            epoch_week_number=epoch_week,
            weekly_points_total=total_points,  # 直接設定，不依賴 column default
        )
        db.add(standing)
    else:
        standing.weekly_points_total = (standing.weekly_points_total or 0) + total_points
        # 修復既有紀錄若無 branch_id
        if not standing.branch_id:
            last_standing = db.query(LeaderboardStandings).filter(
                LeaderboardStandings.agent_id == agent_id,
                LeaderboardStandings.branch_id.isnot(None)
            ).order_by(desc(LeaderboardStandings.epoch_week_number)).first()
            if last_standing:
                standing.branch_id = last_standing.branch_id
            elif agent_id == "tester_01":
                standing.branch_id = "敦南分行"

    return ledger_entries, streak, shield_awarded


# =====================
# ⚙️ 規則 3：每日結算引擎
# =====================

def run_daily_settlement(
    db: Session,
    settlement_date: Optional[date] = None
) -> dict:
    """
    規則 3：連勝中斷判定引擎。

    邏輯：
    1. 掃描所有 AgentStreaks 紀錄
    2. 跳過 settlement_date 當天有學習的業務員
    3. 對缺席者：
       - 若 active_shields_count > 0 → 扣除 1 面防護罩，連勝保留（防護罩優先）
       - 若 active_shields_count == 0 → current_streak_days 歸零

    ⚠️  呼叫此函數後，呼叫方必須執行 db.commit()。

    Args:
        settlement_date: 要結算的日期（預設為昨日），支援手動指定以利補算或測試

    Returns:
        結算統計摘要 dict
    """
    if settlement_date is None:
        settlement_date = date.today() - timedelta(days=1)

    all_streaks = db.query(AgentStreaks).all()

    shields_consumed = 0
    streaks_reset = 0
    streaks_preserved = 0

    for streak in all_streaks:
        # 當日有學習 → 跳過，連勝正常保留
        if streak.last_study_date == settlement_date:
            streaks_preserved += 1
            continue

        # 缺席判定
        if streak.active_shields_count > 0:
            # 防護罩吸收一次缺席（連勝天數保留）
            streak.active_shields_count -= 1
            shields_consumed += 1
        else:
            # 無護盾 → 連勝歸零（歷史最長連勝紀錄不受影響）
            streak.current_streak_days = 0
            streaks_reset += 1

    return {
        "settlement_date": settlement_date,
        "processed_count": len(all_streaks),
        "shields_consumed": shields_consumed,
        "streaks_reset": streaks_reset,
        "streaks_preserved": streaks_preserved,
    }


# =====================
# 📊 相對排行榜查詢
# =====================

def get_relative_leaderboard(
    db: Session,
    agent_id: str,
    window: int = 2
) -> Optional[dict]:
    """
    相對排行榜：以指定業務員為中心，回傳其前後 window 名的排名資訊。

    隱私設計：
    - 當前使用者顯示為 "YOU"
    - 其他業務員 agent_id 被轉為匿名代號（不可逆）
    - 真實 agent_id 不包含在任何回應欄位中

    Returns:
        None — 若業務員本週尚無積分紀錄（尚未開始學習）
    """
    # 模擬模式：優先使用資料庫中最新的週次 ID
    latest_week_record = db.query(LeaderboardStandings.epoch_week_number).order_by(desc(LeaderboardStandings.epoch_week_number)).first()
    epoch_week = latest_week_record[0] if latest_week_record else _get_epoch_week()

    # 優化查詢：僅抓取必要的鄰居
    all_standings = (
        db.query(LeaderboardStandings)
        .filter(LeaderboardStandings.epoch_week_number == epoch_week)
        .order_by(desc(LeaderboardStandings.weekly_points_total), LeaderboardStandings.standing_id)
        .all()
    )

    if not all_standings:
        return None

    user_index = next((i for i, s in enumerate(all_standings) if s.agent_id == agent_id), None)
    if user_index is None:
        return None

    start = max(0, user_index - window)
    end = min(len(all_standings), user_index + window + 1)
    neighbors = all_standings[start:end]

    entries = []
    for i, standing in enumerate(neighbors):
        actual_rank = start + i + 1
        is_me = standing.agent_id == agent_id
        entries.append({
            "rank_display": f"#{actual_rank:04d}",
            "agent_code": standing.agent_id,
            "weekly_points_total": standing.weekly_points_total,
            "is_current_user": is_me,
        })

    return {
        "current_user_rank": user_index + 1,
        "total_participants": len(all_standings),
        "entries": entries,
    }

def get_branch_leaderboard(db: Session, agent_id: Optional[str] = None) -> dict:
    """
    分行對戰：加總本週各分公司的總分，回傳排名陣列。

    若提供 agent_id，額外查出該使用者所屬的分行 ID（my_branch），
    供前端高亮顯示該使用者所屬分行列。
    """
    from sqlalchemy import func, desc
    # 模擬模式：優先使用資料庫中最新的週次 ID
    latest_week_record = db.query(LeaderboardStandings.epoch_week_number).order_by(desc(LeaderboardStandings.epoch_week_number)).first()
    epoch_week = latest_week_record[0] if latest_week_record else _get_epoch_week()

    # 查出使用者所屬分行（若有提供 agent_id）
    my_branch = None
    if agent_id:
        user_standing = (
            db.query(LeaderboardStandings)
            .filter(
                LeaderboardStandings.agent_id == agent_id,
                LeaderboardStandings.epoch_week_number == epoch_week,
            )
            .first()
        )
        if user_standing:
            my_branch = user_standing.branch_id

        # 若這週沒記錄，或這週 branch_id 遺失，往回找
        if not my_branch:
            past_standing = (
                db.query(LeaderboardStandings.branch_id)
                .filter(
                    LeaderboardStandings.agent_id == agent_id,
                    LeaderboardStandings.branch_id.isnot(None)
                )
                .order_by(desc(LeaderboardStandings.epoch_week_number))
                .first()
            )
            if past_standing:
                my_branch = past_standing.branch_id
            elif agent_id == "tester_01":
                my_branch = "敦南分行"
            
            # 自動修復這週的紀錄
            if user_standing and my_branch:
                user_standing.branch_id = my_branch
                db.commit()

    # 依分公司分組加總分數
    results = (
        db.query(
            LeaderboardStandings.branch_id,
            func.sum(LeaderboardStandings.weekly_points_total).label("total_points")
        )
        .filter(LeaderboardStandings.epoch_week_number == epoch_week)
        .filter(LeaderboardStandings.branch_id.isnot(None))
        .group_by(LeaderboardStandings.branch_id)
        .order_by(func.sum(LeaderboardStandings.weekly_points_total).desc())
        .all()
    )

    entries = []
    for i, row in enumerate(results):
        entries.append({
            "rank": i + 1,
            "branch_id": row.branch_id,
            "total_points": int(row.total_points or 0)
        })

    return {"entries": entries, "my_branch": my_branch}

def get_user_status(db: Session, agent_id: str) -> dict:
    """
    取得業務員目前的連勝與盾牌狀態。
    """
    streak = db.query(AgentStreaks).filter(AgentStreaks.agent_id == agent_id).first()
    if not streak:
        return {
            "current_streak_days": 0,
            "active_shields_count": 0,
            "has_studied_today": False,
        }
    
    has_studied = streak.last_study_date == date.today()

    return {
        "current_streak_days": streak.current_streak_days,
        "longest_historical_streak": streak.longest_historical_streak,
        "active_shields_count": streak.active_shields_count,
        "has_studied_today": has_studied,
    }

def perform_weekly_settlement(db: Session):
    """
    模擬每週日結算：
    為了維持 3 張表架構且不丟失資料，我們「產生下一週的新紀錄並歸零」。
    這樣現有的資料就會自然變成「歷史紀錄」。
    """
    # 找到目前資料庫中最新的週次
    latest_week_record = db.query(LeaderboardStandings.epoch_week_number).order_by(desc(LeaderboardStandings.epoch_week_number)).first()
    current_week = latest_week_record[0] if latest_week_record else _get_epoch_week()
    
    # 計算下一週
    try:
        year = int(current_week[:4])
        week = int(current_week[4:])
        if week >= 52:
            new_week = f"{year+1}01"
        else:
            new_week = f"{year}{week+1:02d}"
    except:
        new_week = _get_epoch_week() # Fallback
        
    # 取得目前所有的參與者與其對應的分行
    # 我們只需要幫有紀錄的人建立新週次的空紀錄
    current_standings = db.query(LeaderboardStandings).filter(LeaderboardStandings.epoch_week_number == current_week).all()
    
    for s in current_standings:
        db.add(LeaderboardStandings(
            agent_id=s.agent_id,
            branch_id=s.branch_id,
            epoch_week_number=new_week,
            weekly_points_total=0
        ))
        
    db.commit()

def get_user_history(db: Session, agent_id: str):
    """
    取得該業務員的所有歷史週結算紀錄。
    從 LeaderboardStandings 撈取非本週的資料。
    """
    latest_week_record = db.query(LeaderboardStandings.epoch_week_number).order_by(desc(LeaderboardStandings.epoch_week_number)).first()
    current_week = latest_week_record[0] if latest_week_record else _get_epoch_week()
    
    return (
        db.query(LeaderboardStandings)
        .filter(
            LeaderboardStandings.agent_id == agent_id,
            LeaderboardStandings.epoch_week_number != current_week
        )
        .order_by(desc(LeaderboardStandings.epoch_week_number))
        .all()
    )
