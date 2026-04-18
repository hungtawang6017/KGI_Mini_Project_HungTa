import { useState } from 'react'

const TUTORIAL_PAGES = [
  {
    title: "第一課：加法與減法",
    content: "加法是將兩個數字合併，例如：5 + 3 = 8。減法是從一個數字中拿走另一個數字，例如：10 - 4 = 6。",
    icon: "➕"
  },
  {
    title: "第二課：乘法基礎",
    content: "乘法是重複的加法。例如：3 × 4 表示有 3 個 4 連續相加。熟記九九乘法表能讓你算得更快！",
    icon: "✖️"
  },
  {
    title: "第三課：除法概念",
    content: "除法是將一個數字平分。例如：12 ÷ 3 = 4，表示把 12 顆蘋果平分給 3 個人，每個人可以拿到 4 顆。",
    icon: "➗"
  }
]

export default function MathQuiz({ onComplete, onCancel }) {
  const [step, setStep] = useState('tutorial') // 'tutorial', 'quiz', 'result'
  const [tutorialIndex, setTutorialIndex] = useState(0)
  
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState(['', '', ''])
  
  // 隨機產生 3 題國小數學題
  const generateQuestions = () => {
    const ops = ['+', '-', '*']
    const newQs = []
    for (let i = 0; i < 3; i++) {
      const op = ops[Math.floor(Math.random() * ops.length)]
      let a, b, ans
      if (op === '+') {
        a = Math.floor(Math.random() * 20) + 1
        b = Math.floor(Math.random() * 20) + 1
        ans = a + b
      } else if (op === '-') {
        a = Math.floor(Math.random() * 20) + 10
        b = Math.floor(Math.random() * a) // b <= a
        ans = a - b
      } else {
        a = Math.floor(Math.random() * 9) + 2
        b = Math.floor(Math.random() * 9) + 2
        ans = a * b
      }
      newQs.push({ text: `${a} ${op} ${b} = ?`, answer: ans })
    }
    setQuestions(newQs)
  }

  const handleNextTutorial = () => {
    if (tutorialIndex < TUTORIAL_PAGES.length - 1) {
      setTutorialIndex(prev => prev + 1)
    } else {
      generateQuestions()
      setStep('quiz')
    }
  }

  const handleSubmitQuiz = () => {
    let correctCount = 0
    questions.forEach((q, i) => {
      if (parseInt(answers[i]) === q.answer) {
        correctCount++
      }
    })
    
    // 全對 +5 分，加上原本的基礎 10 分
    const isPerfect = correctCount === questions.length
    
    // 回傳給父元件處理 API 呼叫
    onComplete(isPerfect, correctCount)
  }

  return (
    <div className="quiz-overlay fade-in-up">
      <div className="quiz-modal glass-card">
        
        {/* ── 教學階段 ── */}
        {step === 'tutorial' && (
          <div className="tutorial-step">
            <div className="tutorial-icon bounce">{TUTORIAL_PAGES[tutorialIndex].icon}</div>
            <h3 className="tutorial-title">{TUTORIAL_PAGES[tutorialIndex].title}</h3>
            <p className="tutorial-content">{TUTORIAL_PAGES[tutorialIndex].content}</p>
            
            <div className="tutorial-progress">
              {TUTORIAL_PAGES.map((_, i) => (
                <div key={i} className={`dot ${i === tutorialIndex ? 'active' : ''}`} />
              ))}
            </div>

            <div className="quiz-actions">
              <button className="btn-secondary" onClick={onCancel}>取消</button>
              <button className="btn-primary" onClick={handleNextTutorial}>
                {tutorialIndex < TUTORIAL_PAGES.length - 1 ? '下一頁' : '開始測驗'}
              </button>
            </div>
          </div>
        )}

        {/* ── 測驗階段 ── */}
        {step === 'quiz' && (
          <div className="quiz-step">
            <h3 className="quiz-header">測驗開始 (共 3 題)</h3>
            <p className="quiz-sub">請回答以下數學問題：</p>
            
            <div className="questions-list">
              {questions.map((q, i) => (
                <div key={i} className="question-item">
                  <span className="question-text">Q{i + 1}: {q.text}</span>
                  <input
                    type="number"
                    className="question-input"
                    value={answers[i]}
                    onChange={(e) => {
                      const newAns = [...answers]
                      newAns[i] = e.target.value
                      setAnswers(newAns)
                    }}
                  />
                </div>
              ))}
            </div>

            <div className="quiz-actions">
              <button className="btn-secondary" onClick={onCancel}>放棄</button>
              <button 
                className="btn-primary" 
                onClick={handleSubmitQuiz}
                disabled={answers.some(a => a.trim() === '')}
              >
                交卷
              </button>
            </div>
          </div>
        )}

      </div>

      <style>{`
        .quiz-overlay {
          position: fixed;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(0, 0, 0, 0.75);
          backdrop-filter: blur(8px);
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }
        .quiz-modal {
          width: 100%;
          max-width: 400px;
          padding: 30px 24px;
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        .tutorial-step, .quiz-step {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }
        .tutorial-icon {
          font-size: 3rem;
          margin-bottom: 16px;
        }
        .tutorial-title {
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 12px;
        }
        .tutorial-content {
          font-size: 15px;
          line-height: 1.6;
          color: var(--text-secondary);
          margin-bottom: 24px;
        }
        .tutorial-progress {
          display: flex;
          gap: 8px;
          margin-bottom: 24px;
        }
        .dot {
          width: 8px; height: 8px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.2);
          transition: background 0.3s;
        }
        .dot.active {
          background: var(--color-primary);
        }
        
        .quiz-header {
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 8px;
        }
        .quiz-sub {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 24px;
        }
        .questions-list {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 16px;
          margin-bottom: 24px;
        }
        .question-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: rgba(255, 255, 255, 0.05);
          padding: 12px 16px;
          border-radius: var(--radius-md);
        }
        .question-text {
          font-size: 16px;
          font-weight: 600;
        }
        .question-input {
          width: 80px;
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-sm);
          padding: 8px;
          color: white;
          text-align: center;
          font-size: 16px;
        }
        .question-input:focus {
          outline: none;
          border-color: var(--color-primary);
        }

        .quiz-actions {
          width: 100%;
          display: flex;
          gap: 12px;
        }
        .quiz-actions button {
          flex: 1;
          padding: 12px;
          justify-content: center;
        }
        .bounce {
          animation: bounce 2s infinite ease-in-out;
        }
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  )
}
