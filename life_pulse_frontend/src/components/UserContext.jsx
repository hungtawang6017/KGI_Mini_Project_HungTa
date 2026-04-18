/**
 * UserContext.jsx — 相對排行榜視圖
 *
 * 隱私設計：
 * - 當前使用者顯示為「YOU」+ 高亮背景
 * - 其他人以 AGT-XXXX 匿名代號顯示
 * - 真實姓名永遠不出現在此元件中
 *
 * 視覺邏輯：
 * - 使用者排在中央，上下各最多 2 名鄰居
 * - 當前使用者列有靛紫漸層高亮邊框
 * - 積分以動態數字跳動效果顯示
 */

import { useState } from 'react'

function RankRow({ entry, animateIn, delay = 0 }) {
  const { rank_display, agent_code, weekly_points_total, is_current_user } = entry

  return (
    <div
      className={`rank-row ${is_current_user ? 'rank-row-current' : ''} ${animateIn ? 'fade-in-up' : ''}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className={`rank-badge ${is_current_user ? 'rank-badge-current' : ''}`}>
        {rank_display}
      </div>
      <div className="rank-identity">
        <span className={`rank-name ${is_current_user ? 'rank-name-current' : ''}`}>
          {agent_code}
        </span>
        {is_current_user && <span className="rank-you-tag">本人</span>}
      </div>
      <div className={`rank-points ${is_current_user ? 'text-gradient' : ''}`}>
        {weekly_points_total.toLocaleString()}
        <span className="rank-pts-label">pts</span>
      </div>
    </div>
  )
}

export default function UserContext({ leaderboardData, branchLeaderboardData, historyData = [], agentId, isLoading, tab, setTab }) {

  if (isLoading) {
    return (
      <div className="user-context glass-card">
        <div className="uc-loading">
          <div className="spinner" />
          <span>載入排行榜資料...</span>
        </div>
        <style>{ucStyles}</style>
      </div>
    )
  }

  const renderPersonalLeaderboard = () => {
    if (!leaderboardData) {
      return (
        <div className="uc-empty">
          <div className="uc-empty-icon">🌱</div>
          <p>本週尚無個人排行資料</p>
        </div>
      )
    }
    return (
      <div className="rank-list">
        {leaderboardData.entries.map((entry, i) => (
          <RankRow
            key={entry.rank_display}
            entry={entry}
            animateIn={true}
            delay={i * 60}
          />
        ))}
      </div>
    )
  }

  const renderBranchLeaderboard = () => {
    if (!branchLeaderboardData || branchLeaderboardData.entries.length === 0) {
      return (
        <div className="uc-empty">
          <div className="uc-empty-icon">🏢</div>
          <p>本週尚無分行排行資料</p>
        </div>
      )
    }
    return (
      <div className="rank-list">
        {branchLeaderboardData.entries.map((branch, i) => (
          <div key={branch.branch_id} className="rank-row fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
            <div className="rank-badge">#{branch.rank}</div>
            <div className="rank-identity">
              <span className="rank-name">{branch.branch_id}</span>
            </div>
            <div className="rank-points">
              {branch.total_points.toLocaleString()}
              <span className="rank-pts-label">pts</span>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderHistoryList = () => {
    if (!historyData || historyData.length === 0) {
      return (
        <div className="uc-empty">
          <div className="uc-empty-icon">📜</div>
          <p>尚無歷史結算紀錄</p>
        </div>
      )
    }
    return (
      <div className="rank-list">
        {historyData.map((h, i) => (
          <div key={`${h.epoch_week_number}-${i}`} className="rank-row fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
            <div className="rank-badge">週次 {h.epoch_week_number}</div>
            <div className="rank-identity">
              <span className="rank-name">結算完成</span>
            </div>
            <div className="rank-points">
              {h.final_points.toLocaleString()}
              <span className="rank-pts-label">pts</span>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderContent = () => {
    if (tab === 'history') return renderHistoryList();
    if (tab === 'branch') return renderBranchLeaderboard();
    return renderPersonalLeaderboard();
  }

  return (
    <div className="user-context glass-card">
      {/* 頁籤切換 */}
      <div className="uc-tabs">
        <button 
          key="tab-personal"
          className={`uc-tab ${tab === 'personal' ? 'uc-tab-active' : ''}`}
          onClick={() => setTab('personal')}
        >
          個人排行
        </button>
        <button 
          key="tab-branch"
          className={`uc-tab ${tab === 'branch' ? 'uc-tab-active' : ''}`}
          onClick={() => setTab('branch')}
        >
          分行對戰
        </button>
        <button 
          key="tab-history"
          className={`uc-tab ${tab === 'history' ? 'uc-tab-active' : ''}`}
          onClick={() => setTab('history')}
        >
          歷史紀錄
        </button>
      </div>

      <div className="divider" />

      {/* 列表內容 */}
      <div className="tab-content" style={{ minHeight: '200px' }}>
        {renderContent()}
      </div>

      {/* 隱私聲明 */}
      <div className="uc-privacy-note">
        🔒 {tab === 'personal' ? '僅顯示帳號與相對排名，保護隱私' : tab === 'branch' ? '數據為本週分行累計積分總和' : '顯示您過去每週的最終結算積分'}
      </div>

      <style>{ucStyles}</style>
    </div>
  )
}


const ucStyles = `
  .user-context { padding: 12px 16px 20px; }

  .uc-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
  }
  .uc-tab {
    flex: 1;
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 600;
    padding: 10px 4px;
    cursor: pointer;
    border-radius: 8px;
    transition: all 0.2s;
  }
  .uc-tab:hover { background: rgba(255,255,255,0.03); }
  .uc-tab-active {
    background: rgba(108, 99, 255, 0.1) !important;
    color: var(--accent-secondary);
    box-shadow: inset 0 0 0 1px rgba(108, 99, 255, 0.2);
  }

  .uc-loading, .uc-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 40px 0;
    color: var(--text-secondary);
    font-size: 14px;
  }
  .uc-empty-icon { font-size: 2.5rem; opacity: 0.5; }

  .rank-list { display: flex; flex-direction: column; gap: 6px; }

  .rank-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 16px;
    border-radius: var(--radius-sm);
    background: rgba(255,255,255,0.02);
    border: 1px solid transparent;
  }
  .rank-row-current {
    background: rgba(108, 99, 255, 0.1) !important;
    border-color: rgba(108, 99, 255, 0.35) !important;
  }

  .rank-badge {
    font-family: var(--font-display);
    font-size: 12px;
    font-weight: 700;
    color: var(--text-muted);
    min-width: 40px;
  }
  .rank-badge-current { color: var(--accent-secondary); }

  .rank-identity { flex: 1; display: flex; align-items: center; gap: 8px; }
  .rank-name { font-size: 14px; font-weight: 500; color: var(--text-secondary); }
  .rank-name-current { color: var(--text-primary); font-weight: 700; }
  .rank-you-tag {
    font-size: 10px;
    font-weight: 600;
    background: var(--gradient-primary);
    color: white;
    padding: 2px 8px;
    border-radius: 20px;
  }
  
  .rank-points {
    font-family: var(--font-display);
    font-size: 17px;
    font-weight: 800;
    color: var(--text-secondary);
    display: flex;
    align-items: baseline;
    gap: 3px;
  }
  .rank-pts-label { font-size: 10px; color: var(--text-muted); }

  .uc-privacy-note {
    margin-top: 16px;
    font-size: 11px;
    color: var(--text-muted);
    text-align: center;
  }
`

