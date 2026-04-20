import { useState } from 'react'

export default function Login({ onLogin }) {
  const [agentId, setAgentId] = useState('tester_01')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (agentId.trim()) {
      onLogin(agentId.trim())
    }
  }

  return (
    <div className="login-container">
      <div className="login-card glass-card">
        <div className="brand-logo">
          <span className="brand-icon">⚡</span>
        </div>
        <h1 className="login-title">登入 L.I.F.E. Pulse</h1>
        <p className="login-sub">請輸入您的測試帳號</p>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <input
              type="text"
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              placeholder="輸入 agent_id (例如: tester_01)"
              className="login-input"
              autoFocus
            />
          </div>
          
          <button type="submit" className="btn-primary login-btn">
            進入系統
          </button>
        </form>
        
        <div className="login-hints">
          <p>預設測試帳號：<code>tester_01</code></p>
          <p>無需密碼，直接進入</p>
        </div>
      </div>

      <style>{`
        .login-container {
          min-height: 100dvh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }
        .login-card {
          width: 100%;
          max-width: 360px;
          padding: 40px 30px;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .login-title {
          font-family: var(--font-display);
          font-size: 24px;
          font-weight: 800;
          margin-top: 16px;
          margin-bottom: 8px;
        }
        .login-sub {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 30px;
        }
        .login-form {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .login-input {
          width: 100%;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
          padding: 14px 16px;
          color: var(--text-primary);
          font-size: 16px;
          text-align: center;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .login-input:focus {
          outline: none;
          border-color: var(--color-primary);
          box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.2);
        }
        .login-btn {
          width: 100%;
          padding: 14px;
          font-size: 16px;
          border-radius: var(--radius-md);
          justify-content: center;
        }
        .login-hints {
          margin-top: 30px;
          font-size: 12px;
          color: var(--text-muted);
          line-height: 1.6;
        }
        .login-hints code {
          background: rgba(255, 255, 255, 0.1);
          padding: 2px 6px;
          border-radius: 4px;
        }
      `}</style>
    </div>
  )
}
