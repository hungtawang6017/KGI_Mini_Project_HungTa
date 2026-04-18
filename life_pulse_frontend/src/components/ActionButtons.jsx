/**
 * ActionButtons.jsx — 行動呼籲按鈕區
 *
 * 兩個核心 CTA：
 * 1. ⚡ 開始 7 分鐘學習衝刺 → POST /api/learning/complete-session
 * 2. 🏆 檢視相對排行榜     → GET  /api/leaderboard/relative/{agentId}
 *
 * 設計原則：
 * - 學習衝刺按鈕為最高優先的主要 CTA（靛紫漸層背景）
 * - 按鈕點擊後顯示 Loading 狀態，防止重複提交
 * - 成功後觸發回調，讓父元件更新狀態
 */

import { useState } from 'react'

export default function ActionButtons({
  agentId,
  onSessionComplete,
  onLeaderboardRefresh,
  isSessionLoading,
  isLeaderboardLoading,
  hasStudiedToday,
}) {
  const [sessionCooldown, setSessionCooldown] = useState(false)

  const handleStartSession = async () => {
    if (isSessionLoading || sessionCooldown) return
    // 防抖：同一秒內不能重複點擊
    setSessionCooldown(true)
    setTimeout(() => setSessionCooldown(false), 2000)
    await onSessionComplete()
  }

  return (
    <div className="action-buttons-wrap">

      {/* ── 主要 CTA：學習衝刺 ── */}
      <button
        id="btn-start-session"
        className={`btn-primary btn-cta-main ${hasStudiedToday ? 'btn-completed' : ''}`}
        onClick={handleStartSession}
        disabled={isSessionLoading || sessionCooldown || hasStudiedToday}
        aria-label={hasStudiedToday ? '今天已完成學習' : '開始七分鐘學習衝刺'}
      >
        {isSessionLoading ? (
          <>
            <div className="spinner" />
            <span>記錄中...</span>
          </>
        ) : hasStudiedToday ? (
          <>
            <span className="btn-icon">✅</span>
            <div className="btn-text-block">
              <span className="btn-main-text">(今天已完成學習)</span>
              <span className="btn-sub-text">明天再繼續保持！</span>
            </div>
          </>
        ) : (
          <>
            <span className="btn-icon">⚡</span>
            <div className="btn-text-block">
              <span className="btn-main-text">開始 7 分鐘學習衝刺</span>
              <span className="btn-sub-text">+10 分 · 累積連勝天數</span>
            </div>
          </>
        )}
      </button>

      {/* ── 次要 CTA：排行榜 ── */}
      <button
        id="btn-view-leaderboard"
        className="btn-secondary btn-cta-sub"
        onClick={onLeaderboardRefresh}
        disabled={isLeaderboardLoading}
        aria-label="檢視相對排行榜"
      >
        {isLeaderboardLoading ? (
          <>
            <div className="spinner spinner-sm" />
            <span>載入中...</span>
          </>
        ) : (
          <>
            <span>🏆</span>
            <span>更新排行榜</span>
          </>
        )}
      </button>

      <style>{`
        .action-buttons-wrap {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .btn-cta-main {
          width: 100%;
          padding: 18px 28px;
          font-size: 16px;
          border-radius: var(--radius-lg);
          justify-content: flex-start;
          gap: 16px;
          box-shadow: 0 6px 28px rgba(108, 99, 255, 0.4);
        }
        .btn-icon {
          font-size: 1.5rem;
          filter: drop-shadow(0 0 4px rgba(255,200,0,0.6));
        }
        .btn-text-block {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          text-align: left;
        }
        .btn-main-text {
          font-size: 16px;
          font-weight: 700;
          line-height: 1.2;
        }
        .btn-sub-text {
          font-size: 12px;
          font-weight: 400;
          opacity: 0.75;
          margin-top: 2px;
        }
        .btn-cta-sub {
          width: 100%;
          justify-content: center;
        }
        .btn-completed {
          background: rgba(255, 255, 255, 0.05) !important;
          color: var(--text-muted) !important;
          box-shadow: none !important;
          border: 1px dashed var(--border-subtle) !important;
          cursor: not-allowed;
          opacity: 0.6;
        }
        .btn-completed .btn-icon { filter: grayscale(1) opacity(0.5); }
        .spinner-sm {
          width: 16px;
          height: 16px;
        }
      `}</style>
    </div>
  )
}
