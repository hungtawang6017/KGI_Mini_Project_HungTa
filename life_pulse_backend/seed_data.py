"""
seed_data.py — 國小數學課程測試資料植入腳本
執行: cd life_pulse_backend && python seed_data.py
"""
import os, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from datetime import date, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("❌ 未設定 DATABASE_URL！")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

from models import Base, PointLedger, AgentStreaks, LeaderboardStandings
from crud import _get_epoch_week

# ── 國小數學課程事件清單 ────────────────────────────────────────────
MATH_MODULES = [
    ("加法與減法基礎", "module_completed", 10),
    ("乘法口訣記憶術", "module_completed", 10),
    ("分數的概念入門", "module_completed", 10),
    ("幾何圖形辨識",   "module_completed", 10),
    ("測量單位換算",   "module_completed", 10),
]

BRANCH_NAMES = {
    "dunan":      "敦南分行",
    "zhongshan":  "中山分行",
    "songjiang":  "松江分行",
    "tianmu":     "天母分行",
    "ruiguang":   "瑞光分行",
}

import random

def generate_agents(count=50):
    random.seed(42) # For consistent results
    agents = []
    branches = list(BRANCH_NAMES.keys())
    for i in range(count):
        branch = random.choice(branches)
        streak = random.randint(0, 15)
        # 根據新規則：盾牌上限 1，連勝 >= 3 才有機會獲得
        shields = 1 if streak >= 3 and random.random() > 0.3 else 0
        weekly_pts = random.randint(0, 300)
        longest = max(streak, random.randint(streak, 20))
        agent_id = f"agent_{branch}_{i:02d}"
        
        # 確保 tester_01 存在
        if i == 0:
            agent_id = "tester_01"
            branch = "dunan"
            streak = 2
            shields = 0
            weekly_pts = 80
            longest = 5
            
        agents.append((agent_id, branch, streak, shields, weekly_pts, longest))
    
    # 按分數降序排列，方便預覽
    return sorted(agents, key=lambda x: x[4], reverse=True)

AGENTS = generate_agents(50)

def build_ledger_entries(agent_id: str, weekly_pts: int) -> list:
    """將 weekly_pts 拆解為真實的 PointLedger 事件（事件溯源示範）。"""
    today = date.today()
    entries = []
    remaining = weekly_pts

    # module_completed 每次 10 分
    session_idx = 0
    while remaining >= 10:
        day_ago = min(session_idx // 2, 6)
        module = MATH_MODULES[session_idx % len(MATH_MODULES)]
        entries.append(PointLedger(
            agent_id=agent_id,
            event_type="module_completed",
            points_awarded=10,
        ))
        remaining -= 10
        session_idx += 1

    # 高分者額外補 quiz_perfect (+5) 讓帳本更豐富
    if weekly_pts >= 150:
        for _ in range(weekly_pts // 100):
            entries.append(PointLedger(
                agent_id=agent_id,
                event_type="quiz_perfect",
                points_awarded=5,
            ))

    return entries


def seed():
    # ── 強制刷新 Schema（開發環境適用） ────────────────────────────────
    # 因為 create_all 不會更新現有資料表的欄位，所以先刪除再重建
    temp_db = Session()
    try:
        temp_db.execute(text("DROP TABLE IF EXISTS pointledger CASCADE"))
        temp_db.execute(text("DROP TABLE IF EXISTS agentstreaks CASCADE"))
        temp_db.execute(text("DROP TABLE IF EXISTS leaderboardstandings CASCADE"))
        temp_db.execute(text("DROP TABLE IF EXISTS weeklyhistory CASCADE"))
        temp_db.commit()
        print("🗑️  舊資料表已移除")
    except Exception as e:
        print(f"⚠️  移除資料表時出錯（可能尚不存在）: {e}")
        temp_db.rollback()
    finally:
        temp_db.close()

    Base.metadata.create_all(bind=engine)
    db = Session()
    try:
        epoch_week = _get_epoch_week()
        today = date.today()

        # ── 植入歷史資料（模擬過去兩週） ────────────────────────────────
        from models import WeeklyHistory
        for agent_id, branch_key, _, _, weekly_pts, _ in AGENTS:
            # 隨機產生兩週前的紀錄
            db.add(WeeklyHistory(
                agent_id=agent_id,
                epoch_week_number="202615",
                final_points=random.randint(50, 200),
                settlement_date=today - timedelta(days=14)
            ))
            # 隨機產生上週的紀錄
            db.add(WeeklyHistory(
                agent_id=agent_id,
                epoch_week_number="202616",
                final_points=random.randint(50, 200),
                settlement_date=today - timedelta(days=7)
            ))

        # ── 植入當前週資料 ───────────────────────────────────────────
        for agent_id, branch_key, streak, shields, weekly_pts, longest in AGENTS:
            branch_name = BRANCH_NAMES[branch_key]
            # 1. LeaderboardStandings（本週快取）
            db.add(LeaderboardStandings(
                agent_id=agent_id,
                branch_id=branch_name,
                epoch_week_number=epoch_week,
                weekly_points_total=weekly_pts,
            ))

            # 2. AgentStreaks（狀態機）
            last_study = (today - timedelta(days=1)) if streak > 0 else (today - timedelta(days=3))
            db.add(AgentStreaks(
                agent_id=agent_id,
                current_streak_days=streak,
                longest_historical_streak=longest,
                active_shields_count=shields,
                streak_shield_counter=streak % 3, # 根據當前連勝初始化進度
                last_study_date=last_study,
            ))

            # 3. PointLedger（不可變帳本）
            for entry in build_ledger_entries(agent_id, weekly_pts):
                db.add(entry)

        db.commit()
        print(f"✅ 成功植入 {len(AGENTS)} 位業務員的測試資料！")
        print(f"   本週 epoch_week: {epoch_week}")
        print(f"   分行分布: {', '.join(BRANCH_NAMES.values())}")
        print(f"\n   📊 本週排名預覽：")
        for i, (aid, branch_key, streak, shields, pts, _) in enumerate(AGENTS, 1):
            marker = " ← 您的測試帳號" if aid == "tester_01" else ""
            print(f"   #{i:02d}  {BRANCH_NAMES[branch_key]:<8}  {pts:>4} pts  [Streak: {streak}]  [Shields: {shields}]  {marker}")

    except Exception as e:
        db.rollback()
        print(f"❌ 植入失敗：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
