/**
 * api/client.js — Axios 封裝層
 *
 * 職責：
 * - 統一設定 baseURL，前端永遠不需要硬寫後端位址
 * - 統一錯誤攔截：API 失敗時在 console 輸出可讀的錯誤訊息
 * - 不快取任何敏感個資（Stateless 設計）
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
})

// 回應攔截器：統一錯誤處理
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || '未知錯誤'
    console.error(`[L.I.F.E. Pulse API Error] ${message}`)
    return Promise.reject(error)
  }
)

// ── API 方法封裝 ────────────────────────────────────────────────

/**
 * 完成一次 7 分鐘學習衝刺
 * POST /api/learning/complete-session
 */
export const completeSession = (agentId, eventType = 'COURSE_COMPLETION', isQuizPerfect = false) =>
  apiClient.post('/api/learning/complete-session', {
    agent_id: agentId,
    event_type: eventType,
    is_quiz_perfect: isQuizPerfect
  })

/**
 * 取得業務員當前連勝/盾牌狀態
 */
export const getUserStatus = (agentId) =>
  apiClient.get(`/api/learning/status/${agentId}`)

/**
 * 取得個人歷史週結算紀錄
 */
export const getUserHistory = (agentId) =>
  apiClient.get(`/api/learning/history/${agentId}`)

/**
 * 取得相對排行榜（以當前使用者為中心）
 * GET /api/leaderboard/relative/{agentId}
 */
export const getRelativeLeaderboard = (agentId) =>
  apiClient.get(`/api/leaderboard/relative/${agentId}`)

/**
 * 取得分行對戰排行榜
 * GET /api/leaderboard/branch?agent_id={agentId}
 * 回傳中包含 my_branch，供前端高亮使用者所屬分行
 */
export const getBranchLeaderboard = (agentId = null) =>
  apiClient.get('/api/leaderboard/branch', { params: agentId ? { agent_id: agentId } : {} })

/**
 * 手動觸發每日連勝結算（開發/測試用）
 * POST /api/streak/daily-settlement
 */
export const triggerDailySettlement = (settlementDate = null) =>
  apiClient.post('/api/streak/daily-settlement', {
    settlement_date: settlementDate,
  })

// ── DEV 專用 API ────────────────────────────────────────────────

export const triggerDevSettlement = () =>
  apiClient.post('/api/dev/simulate-settlement')

/**
 * 模擬每週日結算（積分歸零 + 歷史存檔）
 */
export const triggerWeeklySettlement = () =>
  apiClient.post('/api/dev/weekly-settlement')

export const triggerDevSeed = () =>
  apiClient.post('/api/dev/seed')

export const triggerDevBonus = (agentId, bonusType) =>
  apiClient.post(`/api/dev/award-bonus/${agentId}?event_type=${bonusType}`)

export const triggerDevReset = (agentId) =>
  apiClient.post(`/api/dev/reset-agent/${agentId}`)

export const triggerDevIncreaseStreak = (agentId) =>
  apiClient.post(`/api/dev/increase-streak/${agentId}`)

export const triggerDevBreakStreak = (agentId) =>
  apiClient.post(`/api/dev/break-streak/${agentId}`)

export default apiClient
