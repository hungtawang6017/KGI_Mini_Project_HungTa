"""
tests/test_streak.py — 連勝結算引擎邊界測試

測試範圍（規則 3）：
1. 有防護罩時缺席 → 扣除護盾，連勝天數保留
2. 無防護罩時缺席 → current_streak_days 歸零
3. 昨日有學習者 → 完全不受結算影響
4. 混合情境 → 多位業務員同時結算的統計正確性
"""

import datetime
import pytest
from models import AgentStreaks


def make_streak(db, agent_id, streak_days, shields, last_study_offset_days):
    """
    測試輔助函數：快速建立一筆 AgentStreaks 紀錄。
    last_study_offset_days: 最後學習日距今多少天前（0=今天, 1=昨天, 2=前天...）
    """
    streak = AgentStreaks(
        agent_id=agent_id,
        current_streak_days=streak_days,
        longest_historical_streak=streak_days,
        active_shields_count=shields,
        last_study_date=datetime.date.today() - datetime.timedelta(days=last_study_offset_days),
    )
    db.add(streak)
    db.commit()
    return streak


class TestDailySettlement:
    """規則 3：每日連勝中斷判定引擎"""

    def test_shield_consumed_when_missed(self, client, db):
        """
        ★ 規格書邊界測試 1：
        業務員有 1 面防護罩時缺席 → 防護罩從 1 降為 0，連勝天數保留。
        """
        # 設置：連勝 5 天、持有 1 面護盾、前天最後學習（昨日缺席）
        streak = make_streak(db, "agent_has_shield", streak_days=5, shields=1, last_study_offset_days=2)

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        response = client.post("/api/streak/daily-settlement", json={
            "settlement_date": str(yesterday),
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["shields_consumed"] == 1
        assert data["streaks_reset"] == 0

        # 直接驗證資料庫狀態
        db.refresh(streak)
        assert streak.current_streak_days == 5, "防護罩應吸收缺席，連勝天數保留"
        assert streak.active_shields_count == 0, "防護罩應被消耗"

    def test_streak_reset_when_no_shield(self, client, db):
        """
        ★ 規格書邊界測試 2：
        業務員無防護罩且缺席 → current_streak_days 歸零，
        但 longest_historical_streak 歷史紀錄不受影響。
        """
        streak = make_streak(db, "agent_no_shield", streak_days=8, shields=0, last_study_offset_days=2)

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        response = client.post("/api/streak/daily-settlement", json={
            "settlement_date": str(yesterday),
        })

        assert response.status_code == 200
        data = response.json()
        assert data["streaks_reset"] == 1
        assert data["shields_consumed"] == 0

        db.refresh(streak)
        assert streak.current_streak_days == 0, "連勝應歸零"
        assert streak.longest_historical_streak == 8, "歷史最長連勝紀錄不得被清除"

    def test_active_learner_not_affected(self, client, db):
        """昨日有學習的業務員，結算時應完全不受影響"""
        # 昨日有學習（last_study_offset_days=1 = 昨天）
        streak = make_streak(db, "agent_active", streak_days=10, shields=0, last_study_offset_days=1)

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        response = client.post("/api/streak/daily-settlement", json={
            "settlement_date": str(yesterday),
        })

        data = response.json()
        assert data["streaks_preserved"] == 1
        assert data["streaks_reset"] == 0
        assert data["shields_consumed"] == 0

        db.refresh(streak)
        assert streak.current_streak_days == 10, "活躍學習者連勝不應被影響"

    def test_mixed_scenario_settlement(self, client, db):
        """
        混合情境：3 位業務員同時結算
        - A：有護盾 + 缺席 → 護盾消耗，連勝保留
        - B：無護盾 + 缺席 → 連勝歸零
        - C：昨日學習 → 完全不受影響
        """
        yesterday = datetime.date.today() - datetime.timedelta(days=1)

        streak_a = make_streak(db, "agent_A", streak_days=5, shields=2, last_study_offset_days=2)
        streak_b = make_streak(db, "agent_B", streak_days=3, shields=0, last_study_offset_days=2)
        streak_c = make_streak(db, "agent_C", streak_days=7, shields=0, last_study_offset_days=1)

        response = client.post("/api/streak/daily-settlement", json={
            "settlement_date": str(yesterday),
        })

        data = response.json()
        assert data["processed_count"] == 3
        assert data["shields_consumed"] == 1
        assert data["streaks_reset"] == 1
        assert data["streaks_preserved"] == 1

        db.refresh(streak_a)
        db.refresh(streak_b)
        db.refresh(streak_c)

        assert streak_a.current_streak_days == 5 and streak_a.active_shields_count == 1
        assert streak_b.current_streak_days == 0
        assert streak_c.current_streak_days == 7

    def test_default_settlement_date_is_yesterday(self, client, db):
        """不指定 settlement_date 時，預設應結算昨日"""
        # 前天學習（yesterday 缺席）
        streak = make_streak(db, "agent_default_date", streak_days=3, shields=1, last_study_offset_days=2)

        # 不帶 settlement_date 參數
        response = client.post("/api/streak/daily-settlement", json={})

        data = response.json()
        assert response.status_code == 200
        # 昨日缺席，護盾應被消耗
        assert data["shields_consumed"] == 1
