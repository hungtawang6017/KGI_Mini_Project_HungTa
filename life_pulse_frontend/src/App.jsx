/**
 * App.jsx — L.I.F.E. Pulse 主應用頁面
 *
 * 架構：
 * - 單一頁面，模擬已登入的業務員 (agentId = 'demo_agent_001')
 * - 狀態：streakDays, shieldCount, leaderboardData, toasts
 * - 事件流：按鈕點擊 → API 呼叫 → 狀態更新 → 視覺回饋
 */

import { useState, useCallback, useEffect } from 'react'
import './App.css'
import StatusBar from './components/StatusBar'
import UserContext from './components/UserContext'
import ActionButtons from './components/ActionButtons'
import DevTools from './components/DevTools'
import Login from './components/Login'
import MathQuiz from './components/MathQuiz'
import { completeSession, getRelativeLeaderboard, getBranchLeaderboard, getUserStatus, getUserHistory } from './api/client'

// ── Toast 通知系統 ──────────────────────────────────────────────
let toastId = 0
function useToast() {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((message, type = 'success') => {
    const id = ++toastId
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 4000)
  }, [])

  return { toasts, addToast }
}

// ── 主元件 ─────────────────────────────────────────────────────
export default function App() {
  const [loggedInAgent, setLoggedInAgent] = useState(null)
  const [showQuiz, setShowQuiz]           = useState(false)
  const [streakDays, setStreakDays]       = useState(0)
  const [longestStreak, setLongestStreak] = useState(0)
  const [shieldCount, setShieldCount]     = useState(0)
  const [leaderboardData, setLeaderboard] = useState(null)
  const [sessionLoading, setSessionLoading]   = useState(false)
  const [lbLoading, setLbLoading]             = useState(false)
  const [lastPoints, setLastPoints]           = useState(null)
  const [tab, setTab]                         = useState('personal') // 'personal' | 'branch'
  const [branchLeaderboardData, setBranchLeaderboard] = useState(null)
  const [hasStudiedToday, setHasStudiedToday] = useState(false)
  const [historyData, setHistoryData]           = useState([])
  const { toasts, addToast } = useToast()



  // ── 取得相對排行榜 ────────────────────────────────────────────
  const fetchLeaderboard = useCallback(async () => {
    if (!loggedInAgent) return
    setLbLoading(true)
    try {
      const res = await getRelativeLeaderboard(loggedInAgent)
      setLeaderboard(res.data)
    } catch {
      setLeaderboard(null)
    } finally {
      setLbLoading(false)
    }
  }, [loggedInAgent])

  const fetchUserStatus = useCallback(async () => {
    if (!loggedInAgent) return
    try {
      const res = await getUserStatus(loggedInAgent)
      setStreakDays(res.data.current_streak_days)
      setLongestStreak(res.data.longest_historical_streak)
      setShieldCount(res.data.active_shields_count)
      setHasStudiedToday(res.data.has_studied_today)
    } catch (err) {
      console.error("Failed to fetch user status", err)
    }
  }, [loggedInAgent])

  const fetchUserHistory = useCallback(async () => {
    if (!loggedInAgent) return
    try {
      const res = await getUserHistory(loggedInAgent)
      setHistoryData(res.data)
    } catch (err) {
      console.error("Failed to fetch user history", err)
    }
  }, [loggedInAgent])

  const fetchBranchLeaderboard = useCallback(async () => {
    setLbLoading(true)
    try {
      const res = await getBranchLeaderboard()
      setBranchLeaderboard(res.data)
    } catch {
      setBranchLeaderboard(null)
    } finally {
      setLbLoading(false)
    }
  }, [])

  const refreshAllData = useCallback(async () => {
    await Promise.all([fetchLeaderboard(), fetchBranchLeaderboard(), fetchUserStatus(), fetchUserHistory()])
  }, [fetchLeaderboard, fetchBranchLeaderboard, fetchUserStatus, fetchUserHistory])

  // 初次載入時嘗試取得排行榜
  useEffect(() => {
    if (loggedInAgent) {
      refreshAllData()
    }
  }, [loggedInAgent, refreshAllData])

  // ── 完成學習衝刺 ──────────────────────────────────────────────
  const handleCompleteSession = useCallback(async (isPerfect, correctCount) => {
    setSessionLoading(true)
    setShowQuiz(false)
    try {
      const res = await completeSession(loggedInAgent, 'COURSE_COMPLETION', isPerfect)
      const { points_awarded, streak } = res.data

      // 更新狀態
      setStreakDays(streak.current_streak_days)
      setLongestStreak(streak.longest_historical_streak)
      setShieldCount(streak.active_shields_count)
      setHasStudiedToday(true)
      setLastPoints(points_awarded)

      // Toast 回饋
      if (isPerfect) {
        addToast(`✅ 完美！測驗全對！總共獲得 +${points_awarded} 積分！連勝 ${streak.current_streak_days} 天`, 'success')
      } else {
        addToast(`✅ 完成學習！獲得 +${points_awarded} 積分！連勝 ${streak.current_streak_days} 天`, 'success')
      }

      if (streak.shield_awarded) {
        setTimeout(() => addToast('🛡️ 恭喜！達成連勝目標，防護罩 +1！', 'shield'), 600)
      }

      // 更新排行榜
      await refreshAllData()

    } catch (err) {
      addToast('❌ 記錄失敗，請稍後再試', 'error')
    } finally {
      setSessionLoading(false)
    }
  }, [addToast, loggedInAgent, fetchLeaderboard])

  // ── 日期顯示 ──────────────────────────────────────────────────
  const today = new Date().toLocaleDateString('zh-TW', {
    year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
  })

  if (!loggedInAgent) {
    return <Login onLogin={setLoggedInAgent} />
  }

  return (
    <>
      {showQuiz && (
        <MathQuiz 
          onComplete={handleCompleteSession} 
          onCancel={() => setShowQuiz(false)} 
        />
      )}
      {/* ── Toast 通知容器 ── */}
      <div className="toast-container" role="status" aria-live="polite">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>{t.message}</div>
        ))}
      </div>

      {/* ── 主要 Layout ── */}
      <div className="app-layout">

        {/* ── Header ── */}
        <header className="app-header">
          <div className="header-brand">
            <div className="brand-logo">
              <span className="brand-icon">💡</span>
            </div>
            <div>
              <h1 className="brand-name">L.I.F.E. P u l s e</h1>
              {/* <p className="brand-tagline">對抗遺忘曲線，攻佔零碎時間</p> */}
            </div>
          </div>
          <div className="header-date">{today}</div>
        </header>

        {/* ── 主內容 ── */}
        <main className="app-main">

          {/* ── Hero 標語 ── */}
          <div className="hero-section fade-in-up">
            <h2 className="hero-title">
              Every Little Bit Makes a 
              <span className="text-gradient">  Difference</span>
            </h2>
            <p className="hero-sub">
              每天累積 7 分鐘的小進步，成就更棒的自己！
            </p>
          </div>

          {/* ── 積分回饋橫幅 ── */}
          {lastPoints && (
            <div className="points-banner glass-card success-burst">
              <span className="points-banner-icon">🎯</span>
              <div>
                <div className="points-banner-value text-gradient">+{lastPoints} 積分</div>
                <div className="points-banner-sub">已寫入不可變積分帳本</div>
              </div>
            </div>
          )}

          {/* ── 狀態列 ── */}
          <div className="fade-in-up" style={{ animationDelay: '100ms' }}>
            <StatusBar 
              streakDays={streakDays} 
              shieldCount={shieldCount} 
              longestStreak={longestStreak} 
            />
          </div>

          {/* ── 行動按鈕 ── */}
          <div className="fade-in-up" style={{ animationDelay: '200ms' }}>
            <ActionButtons
              agentId={loggedInAgent}
              onSessionComplete={() => setShowQuiz(true)}
              onLeaderboardRefresh={fetchLeaderboard}
              isSessionLoading={sessionLoading}
              isLeaderboardLoading={lbLoading}
              hasStudiedToday={hasStudiedToday}
            />
          </div>

          {/* ── 排行榜區域 ── */}
          <div className="fade-in-up" style={{ animationDelay: '300ms' }}>
            <UserContext
              leaderboardData={leaderboardData}
              branchLeaderboardData={branchLeaderboardData}
              historyData={historyData}
              agentId={loggedInAgent}
              isLoading={lbLoading}
              tab={tab}
              setTab={setTab}
            />
          </div>

          {/* ── 底部說明 ── */}
          <div className="footer-note">
            <p>此平台嚴格遵循資安規範 · 積分採不可變帳本設計</p>
            <p>每週日 23:59 自動結算連勝狀態 · 盾牌保護你日常突如其來的忙碌</p>
          </div>

        </main>

        <DevTools 
          agentId={loggedInAgent} 
          onActionComplete={() => {
            refreshAllData();
            setLastPoints(null);
          }}
          addToast={addToast}
        />
      </div>

      <style>{`
        .app-layout {
          max-width: 480px;
          margin: 0 auto;
          min-height: 100dvh;
          padding: 0 0 40px;
          display: flex;
          flex-direction: column;
        }

        /* ── Header ── */
        .app-header {
          position: sticky;
          top: 0;
          z-index: 100;
          background: rgba(5, 8, 15, 0.85);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-bottom: 1px solid var(--border-subtle);
          padding: 16px 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .header-brand { display: flex; align-items: center; gap: 12px; }
        .brand-logo {
          width: 42px; height: 42px;
          background: var(--gradient-primary);
          border-radius: 12px;
          display: flex; align-items: center; justify-content: center;
          font-size: 1.3rem;
          box-shadow: 0 4px 14px rgba(108,99,255,0.4);
        }
        .brand-name {
          font-family: var(--font-display);
          font-size: 18px;
          font-weight: 800;
          background: var(--gradient-primary);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          line-height: 1.2;
        }
        .brand-tagline {
          font-size: 11px;
          color: var(--text-muted);
          letter-spacing: 0.04em;
          margin-top: 2px;
        }
        .header-date {
          font-size: 11px;
          color: var(--text-muted);
          text-align: right;
          line-height: 1.4;
        }

        /* ── Main ── */
        .app-main {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 16px;
          padding: 24px 20px;
        }

        /* ── Hero ── */
        .hero-section { text-align: center; padding: 8px 0 4px; }
        .hero-title {
          font-family: var(--font-display);
          font-size: 26px;
          font-weight: 800;
          line-height: 1.3;
          margin-bottom: 10px;
        }
        .hero-sub {
          font-size: 14px;
          color: var(--text-secondary);
          line-height: 1.6;
        }

        /* ── 積分橫幅 ── */
        .points-banner {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 14px 20px;
          border-color: rgba(45, 212, 191, 0.25) !important;
          background: rgba(45, 212, 191, 0.06) !important;
        }
        .points-banner-icon { font-size: 1.8rem; }
        .points-banner-value {
          font-family: var(--font-display);
          font-size: 22px;
          font-weight: 800;
        }
        .points-banner-sub { font-size: 12px; color: var(--text-muted); }

        /* ── Footer ── */
        .footer-note {
          text-align: center;
          font-size: 11px;
          color: var(--text-muted);
          line-height: 1.8;
          padding-top: 8px;
        }
      `}</style>
    </>
  )
}
