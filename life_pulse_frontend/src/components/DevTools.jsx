import { useState } from 'react'
import { triggerDevSettlement, triggerDevSeed, triggerDevBonus, triggerDevReset, triggerDevIncreaseStreak, triggerDevBreakStreak, completeSession, triggerWeeklySettlement } from '../api/client'

export default function DevTools({ agentId, onActionComplete, addToast }) {
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)

  const handleAction = async (actionFn, successMsg) => {
    setLoading(true)
    try {
      await actionFn()
      addToast(successMsg, 'success')
      if (onActionComplete) onActionComplete()
    } catch (err) {
      addToast(`❌ 執行失敗: ${err.response?.data?.detail || err.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button 
        className="dev-tools-toggle" 
        onClick={() => setOpen(true)}
        title="開發測試工具"
      >
        🛠️
      </button>
    )
  }

  return (
    <div className="dev-tools glass-card">
      <div className="dev-header">
        <h4>🛠️ 開發/測試面板</h4>
        <button className="dev-close" onClick={() => setOpen(false)}>×</button>
      </div>
      
      <div className="dev-buttons">
        <button 
          className="dev-btn dev-btn-warning"
          onClick={() => handleAction(triggerDevSeed, '✅ 已植入測試資料')}
          disabled={loading}
        >
          重新載入預設狀態
        </button>

        <button 
          className="dev-btn dev-btn-warning"
          onClick={() => handleAction(triggerWeeklySettlement, '📅 已模擬每週日結算，積分歸零')}
          disabled={loading}
        >
          模擬每週日 23:59 結算
        </button>
        
        <button 
          className="dev-btn dev-btn-primary"
          onClick={() => handleAction(() => completeSession(agentId, 'COURSE_COMPLETION', false), '⚡ 完成教學 +10 積分！')}
          disabled={loading}
        >
          完成教學 (+10)
        </button>

        <button 
          className="dev-btn dev-btn-primary"
          onClick={() => handleAction(() => triggerDevBonus(agentId, 'quiz_perfect'), '🎯 滿分測驗 +5 積分！')}
          disabled={loading}
        >
          模擬滿分測驗 (+5)
        </button>
        
        <button 
          className="dev-btn dev-btn-primary"
          onClick={() => handleAction(() => triggerDevBonus(agentId, 'bio_rhythm_bonus'), '🧬 生理節律加成 +2 積分！')}
          disabled={loading}
        >
          模擬生理節律加成 (+2)
        </button>

      <button 
          className="dev-btn dev-btn-primary"
          onClick={() => handleAction(() => triggerDevIncreaseStreak(agentId), '🔥 連續學習天數 +1！')}
          disabled={loading}
        >
          增加連續學習天數
        </button>

        <button 
          className="dev-btn dev-btn-danger"
          onClick={() => handleAction(() => triggerDevBreakStreak(agentId), '💔 連續學習已中斷')}
          disabled={loading}
        >
          連續學習中斷
        </button>
      </div>

      <style>{`
        .dev-tools-toggle {
          position: fixed;
          bottom: 20px;
          right: 20px;
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: var(--bg-surface);
          border: 1px solid var(--border-accent);
          color: white;
          font-size: 1.2rem;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(0,0,0,0.5);
          z-index: 1000;
          transition: transform 0.2s;
        }
        .dev-tools-toggle:hover {
          transform: scale(1.1);
        }
        .dev-tools {
          position: fixed;
          bottom: 20px;
          right: 20px;
          width: 280px;
          padding: 16px;
          z-index: 1000;
          border: 1px solid var(--border-accent);
          background: rgba(10, 15, 30, 0.95);
        }
        .dev-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          border-bottom: 1px solid var(--border-subtle);
          padding-bottom: 8px;
        }
        .dev-header h4 {
          margin: 0;
          font-size: 14px;
          color: var(--accent-secondary);
        }
        .dev-close {
          background: none;
          border: none;
          color: var(--text-muted);
          font-size: 1.2rem;
          cursor: pointer;
        }
        .dev-close:hover { color: white; }
        .dev-buttons {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .dev-btn {
          background: var(--bg-surface);
          border: 1px solid var(--border-subtle);
          color: var(--text-primary);
          padding: 8px;
          border-radius: 4px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .dev-btn:hover:not(:disabled) {
          border-color: var(--accent-primary);
          background: rgba(108, 99, 255, 0.1);
        }
        .dev-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .dev-btn-primary { border-color: var(--shield-blue); color: #93c5fd; }
        .dev-btn-warning { border-color: var(--accent-orange); color: #fdba74; }
        .dev-btn-danger  { border-color: var(--accent-red); color: #fca5a5; }
      `}</style>
    </div>
  )
}
