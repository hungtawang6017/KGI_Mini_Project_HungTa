"""
tests/test_learning.py — 學習積分 API 正向測試

測試範圍：
1. 完成課程 → PointLedger 正確寫入 +10 積分（正向路徑）
2. 連勝第 3 天 → 自動觸發防護罩發放（規則 2 邊界測試）
3. 同日重複學習 → 連勝天數不重複計算（冪等性驗證）
"""

import datetime
import pytest
from models import PointLedger, AgentStreaks


class TestCompleteLearningSession:
    """規則 1：積分派發正向測試"""

    def test_complete_session_returns_success(self, client):
        """呼叫 API 後應回傳 200 OK 且 success=True"""
        response = client.post("/api/learning/complete-session", json={
            "agent_id": "agent_001",
            "event_type": "COURSE_COMPLETION",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_complete_session_awards_10_points(self, client):
        """規格要求每次完成課程獎勵 10 積分"""
        response = client.post("/api/learning/complete-session", json={
            "agent_id": "agent_002",
            "event_type": "COURSE_COMPLETION",
        })
        data = response.json()
        assert data["points_awarded"] == 10

    def test_complete_session_writes_to_pointledger(self, client, db):
        """
        ★ 規格書正向測試：
        完成課程後，pointledger 資料表應有且僅有一筆 +10 的不可變紀錄。
        """
        agent_id = "agent_ledger_test"
        client.post("/api/learning/complete-session", json={
            "agent_id": agent_id,
            "event_type": "COURSE_COMPLETION",
        })

        # 直接查詢資料庫驗證
        entries = db.query(PointLedger).filter(PointLedger.agent_id == agent_id).all()

        assert len(entries) == 1, "PointLedger 應有且僅有一筆紀錄"
        assert entries[0].points_awarded == 10
        assert entries[0].event_type == "COURSE_COMPLETION"
        assert entries[0].transaction_id is not None, "transaction_id 應由資料庫自動產生"

    def test_complete_session_creates_streak_record(self, client, db):
        """首次學習應初始化 AgentStreaks 紀錄，連勝天數為 1"""
        agent_id = "agent_first_time"
        client.post("/api/learning/complete-session", json={
            "agent_id": agent_id,
            "event_type": "COURSE_COMPLETION",
        })

        streak = db.query(AgentStreaks).filter(AgentStreaks.agent_id == agent_id).first()
        assert streak is not None, "AgentStreaks 紀錄應被建立"
        assert streak.current_streak_days == 1
        assert streak.last_study_date == datetime.date.today()

    def test_same_day_repetition_does_not_increment_streak(self, client, db):
        """
        冪等性測試：同一天學習兩次，連勝天數應只計算一次（防止刷分）。
        但 PointLedger 應有兩筆紀錄（每次完成都記帳）。
        """
        agent_id = "agent_idempotent"
        # 第一次學習
        client.post("/api/learning/complete-session", json={"agent_id": agent_id})
        # 第二次學習（同日）
        client.post("/api/learning/complete-session", json={"agent_id": agent_id})

        streak = db.query(AgentStreaks).filter(AgentStreaks.agent_id == agent_id).first()
        ledger_count = db.query(PointLedger).filter(PointLedger.agent_id == agent_id).count()

        assert streak.current_streak_days == 1, "同日重複學習不應重複計算連勝"
        assert ledger_count == 2, "PointLedger 應忠實記錄每一次積分事件"


class TestShieldAward:
    """規則 2：連勝達 3 天自動發放防護罩"""

    def test_shield_awarded_on_streak_day_3(self, client, db):
        """
        ★ 規格書邊界測試：
        業務員連勝第 3 天完成學習時，shield_awarded 應為 True，
        active_shields_count 應從 0 增加為 1。
        """
        agent_id = "agent_shield_award"

        # 預先設定連勝天數為 2（模擬前兩天已學習）
        existing_streak = AgentStreaks(
            agent_id=agent_id,
            current_streak_days=2,
            longest_historical_streak=2,
            active_shields_count=0,
            last_study_date=datetime.date.today() - datetime.timedelta(days=1),
        )
        db.add(existing_streak)
        db.commit()

        # 第 3 天學習（透過 API 觸發）
        response = client.post("/api/learning/complete-session", json={
            "agent_id": agent_id,
            "event_type": "COURSE_COMPLETION",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["streak"]["shield_awarded"] is True, "連勝第 3 天應觸發防護罩發放"
        assert data["streak"]["active_shields_count"] == 1
        assert data["streak"]["current_streak_days"] == 3

    def test_no_shield_on_streak_day_2(self, client, db):
        """連勝第 2 天不應觸發防護罩（必須是 3 的倍數）"""
        agent_id = "agent_no_shield_yet"

        existing_streak = AgentStreaks(
            agent_id=agent_id,
            current_streak_days=1,
            longest_historical_streak=1,
            active_shields_count=0,
            last_study_date=datetime.date.today() - datetime.timedelta(days=1),
        )
        db.add(existing_streak)
        db.commit()

        response = client.post("/api/learning/complete-session", json={"agent_id": agent_id})
        data = response.json()

        assert data["streak"]["shield_awarded"] is False
        assert data["streak"]["active_shields_count"] == 0

    def test_second_shield_awarded_on_streak_day_6(self, client, db):
        """連勝第 6 天應再次觸發防護罩（6 是 3 的倍數）"""
        agent_id = "agent_double_shield"

        existing_streak = AgentStreaks(
            agent_id=agent_id,
            current_streak_days=5,
            longest_historical_streak=5,
            active_shields_count=1,  # 已持有第一面護盾
            last_study_date=datetime.date.today() - datetime.timedelta(days=1),
        )
        db.add(existing_streak)
        db.commit()

        response = client.post("/api/learning/complete-session", json={"agent_id": agent_id})
        data = response.json()

        assert data["streak"]["shield_awarded"] is True
        assert data["streak"]["active_shields_count"] == 2
