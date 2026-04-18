/**
 * StatusBar.jsx — 連勝火焰 × 防護罩狀態列
 *
 * 視覺邏輯：
 * - 連勝天數 > 0：顯示跳動火焰 + 橘色漸層數字
 * - 有防護罩：藍色發光盾牌圖示（帶脈衝動畫）
 * - 無防護罩：半透明灰色盾牌
 * - 連勝 = 0：熄火，顯示「開始你的第一天」提示
 */

import { useEffect, useRef, useState } from 'react'

export default function StatusBar({ streakDays = 0, shieldCount = 0, longestStreak = 0, shieldCounter = 0 }) {
  const isOnFire = streakDays > 0
  const hasShield = shieldCount > 0

  return (
    <div className="status-container fade-in-up">
      {/* ── 連勝火焰 ── */}
      <div className="status-badge streak-badge glass-card">
        <span className={`status-icon ${isOnFire ? 'fire-active' : 'fire-inactive'}`}>
          {isOnFire ? '🔥' : '💤'}
        </span>
        <div className="status-text">
          <span className="status-value">x {streakDays}</span>
          <span className="status-label">{isOnFire ? '連勝天數' : '休眠中'}</span>
          <span className="status-longest">歷史最長: {longestStreak} 天</span>
        </div>
      </div>

      {/* ── 防護罩 ── */}
      <div className={`status-badge shield-badge glass-card ${hasShield ? 'shield-on' : ''}`}>
        <span className={`status-icon ${hasShield ? 'shield-active' : 'shield-inactive'}`}>
          🛡️
        </span>
        <div className="status-text">
          <span className="status-value">{hasShield ? '已啟動' : '未獲得'}</span>
          <span className="status-label">防護罩</span>
          <span className="status-counter">進度: {shieldCounter}/3</span>
        </div>
      </div>

      <style>{`
        .status-container {
          display: flex;
          gap: 12px;
          margin: 8px 0;
        }
        .status-badge {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 14px 18px;
          border-radius: 16px;
          transition: all 0.4s var(--ease-spring);
        }
        .status-icon {
          font-size: 1.8rem;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .status-text {
          display: flex;
          flex-direction: column;
        }
        .status-value {
          font-family: var(--font-display);
          font-size: 18px;
          font-weight: 800;
          color: var(--text-primary);
        }
        .status-label {
          font-size: 11px;
          color: var(--text-muted);
          font-weight: 500;
        }
        .status-longest, .status-counter {
          font-size: 9px;
          color: var(--text-muted);
          opacity: 0.6;
          margin-top: 1px;
        }

        /* 火焰動畫 */
        .fire-active {
          filter: drop-shadow(0 0 8px rgba(255, 107, 0, 0.4));
          animation: flame-pulse 1.5s infinite ease-in-out;
        }
        .fire-inactive { opacity: 0.3; }

        @keyframes flame-pulse {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 8px rgba(255, 107, 0, 0.4)); }
          50% { transform: scale(1.1); filter: drop-shadow(0 0 15px rgba(255, 107, 0, 0.6)); }
        }

        /* 盾牌動畫 */
        .shield-active {
          color: var(--shield-blue);
          filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.6));
          animation: shield-pulse 2s infinite ease-in-out;
        }
        .shield-inactive { opacity: 0.2; }

        @keyframes shield-pulse {
          0%, 100% { filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.5)); }
          50% { filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.8)); }
        }

        .shield-on {
          background: rgba(59, 130, 246, 0.15) !important;
        }
        
      `}</style>
    </div>
  )
}
