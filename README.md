# L.I.F.E. Pulse — 遊戲化微學習系統

> **L**earn · **I**nternalize · **F**ocus · **E**volve  

---

## 系統簡介

L.I.F.E. Pulse 是一套**遊戲化微學習平台**，專為金融業務員設計。透過「連勝火焰」、「防護罩」和「積分排行榜」等遊戲化機制，幫助學員建立每日學習習慣。

### 核心遊戲化規則

| 規則 | 機制 | 說明 |
|------|------|------|
| 規則 1 | 完成學習 +10 積分 | 答對所有題目再 +5 分 |
| 規則 2 | 連續學習 +2 積分 | 每天連續登入額外獎勵 |
| 規則 3 | 連勝 3 天獲盾牌 | 盾牌在缺課時保護連勝不歸零 |
| 規則 4 | 每日 23:59 自動結算 | 超過 24 小時未學習則扣盾或斷連 |

---

## 專案結構

```
mini_project_王泓達/
│
├── README.md                    ← 本檔案（整體說明）
├── test_api.py                  ← API 快速測試腳本
│
├── life_pulse_backend/          ← 後端 (Python + FastAPI)
│   ├── README.md                ← 後端詳細說明
│   ├── main.py                  ← 伺服器啟動入口
│   ├── database.py              ← 資料庫引擎（自動偵測 PostgreSQL / SQLite）
│   ├── models.py                ← 資料庫三張表的 ORM 定義
│   ├── schemas.py               ← API 請求/回應格式（Pydantic）
│   ├── crud.py                  ← 核心業務邏輯（積分、連勝、排行榜）
│   ├── seed_data.py             ← 測試資料植入腳本
│   ├── requirements.txt         ← Python 套件清單
│   ├── .env.example             ← 環境變數範本
│   ├── .env                     ← 🔒 實際設定檔（不上傳 Git）
│   └── routers/
│       ├── learning.py          ← 學習引擎 API（加分、查狀態、查歷史）
│       ├── leaderboard.py       ← 排行榜 API（相對排名、分行對戰）
│       ├── streak.py            ← 連勝結算 API
│       └── dev.py               ← 🛠️ 開發測試 API（重置、模擬結算等）
│
└── life_pulse_frontend/         ← 前端 (React + Vite)
    ├── README.md                ← 前端詳細說明
    ├── index.html               ← HTML 入口
    ├── vite.config.js           ← Vite 打包設定
    ├── package.json             ← 套件清單
    └── src/
        ├── main.jsx             ← React 掛載點
        ├── App.jsx              ← 主應用程式（狀態管理中心）
        ├── App.css              ← 全域樣式
        ├── index.css            ← CSS 設計系統（色彩/字體變數）
        ├── api/
        │   └── client.js        ← Axios API 封裝（所有 HTTP 請求）
        └── components/
            ├── Login.jsx        ← 登入頁面
            ├── StatusBar.jsx    ← 連勝火焰 🔥 + 盾牌 🛡️ 狀態列
            ├── ActionButtons.jsx ← 「開始學習」「查看排行榜」按鈕
            ├── MathQuiz.jsx     ← 7 分鐘數學答題模組
            ├── UserContext.jsx  ← 個人/分行排行榜 + 歷史紀錄
            └── DevTools.jsx     ← 🛠️ 開發者工具面板（左下角）
```

---

## 資料庫架構（三表設計）

系統採用**三張核心資料表**，架構精簡但功能完整：

```
┌─────────────────────┐    ┌─────────────────────┐    ┌──────────────────────────┐
│     PointLedger      │    │    AgentStreaks       │    │   LeaderboardStandings   │
│   （積分帳本）        │    │  （連勝狀態機）       │    │  （週排行榜 + 歷史紀錄）  │
├─────────────────────┤    ├─────────────────────┤    ├──────────────────────────┤
│ transaction_id (PK) │    │ streak_id (PK)       │    │ standing_id (PK)          │
│ agent_id            │    │ agent_id (UNIQUE)    │    │ agent_id                  │
│ event_type          │    │ current_streak_days  │    │ branch_id                 │
│ points_awarded      │    │ longest_historical_  │    │ epoch_week_number         │
│ created_at          │    │   streak             │    │   (e.g. "202616")         │
│                     │    │ active_shields_count │    │ weekly_points_total       │
│ 📌 Append-only！    │    │ last_study_date      │    │                           │
│   不可修改、不可刪除  │    │                     │    │ 📌 同一張表同時儲存        │
└─────────────────────┘    └─────────────────────┘    │   本週與歷史資料           │
                                                        └──────────────────────────┘
```

> **週次識別碼說明**：`epoch_week_number` 格式為 `YYYYWW`（例如 `202616` = 2026 年第 16 週）。
> 當期週次的紀錄 = 本週積分；其他週次的紀錄 = 歷史存檔。

---

## 快速啟動（5 步驟）

### 前置需求

| 工具 | 最低版本 | 開發測試版本 | 備註 |
|------|---------|------------|------|
| Python | 3.10+ | 3.13.3 | 必要 |
| Node.js | 18+ | 24.13.1 | 必要 |
| npm | 8+ | 11.8.0 | 隨 Node.js 安裝 |
| PostgreSQL | 14+ | — | **選用**，未安裝時自動改用 SQLite |

> ⚠️ **APScheduler 版本說明**：本專案使用 APScheduler **4.x alpha 預覽版**（`4.0.0a6`），安裝時必須加上 `--pre` 旗標。PyPI 上目前尚無 4.x stable release。

---

### Step 1：下載專案

```bash
git clone https://github.com/hungtawang6017/KGI_Mini_Project_HungTa
cd KGI_Mini_Project_HungTa
```

---

### Step 2：啟動後端（含虛擬環境）

使用 Python 虛擬環境可確保套件版本隔離，不污染系統環境，**強烈建議每台電腦都使用此方式**。

```bash
# 進入後端目錄
cd life_pulse_backend

# ── 建立虛擬環境（只需執行一次）──
py -m venv .venv

# ── 啟動虛擬環境 ──
# Windows（PowerShell）：
.venv\Scripts\Activate.ps1
# Windows（CMD）：
# .venv\Scripts\activate.bat
# macOS / Linux：
# source .venv/bin/activate

# ── 安裝 Python 套件 ──
# 注意：apscheduler 4.x 為 alpha 預覽版，必須加 --pre
pip install --pre -r requirements.txt

# 設定資料庫（二擇一）
# ── 選項 A：有 PostgreSQL ──
copy .env.example .env
# 用任何文字編輯器打開 .env，填入你的 PostgreSQL 連線字串

# ── 選項 B：無資料庫（DEMO 模式）──
# 直接跳過，無需任何設定！系統會自動建立 demo.db

# 植入測試資料（首次使用必做）
py seed_data.py

# 啟動伺服器
uvicorn main:app --reload
```

✅ 後端啟動成功後，可開啟 http://localhost:8000/docs 查看完整 API 文件。

---

### Step 3：啟動前端

**開啟另一個終端機視窗**，執行：

```bash
# 進入前端目錄
cd life_pulse_frontend

# 安裝 Node.js 套件（package-lock.json 會鎖定確切版本）
npm install

# 啟動開發伺服器
npm run dev
```

✅ 前端啟動成功後，開啟瀏覽器前往 http://localhost:5173

---

### Step 4：登入系統

在登入畫面輸入任意業務員 ID（如 `tester_01`）即可進入。

> 如果您已執行過 `python seed_data.py`，預設測試帳號包括：
> `tester_01`、`agent_ruiguang_01`⋯`agent_ruiguang_40`

---

### Step 5：開始使用！

| 功能 | 操作方式 |
|------|---------|
| 完成學習並加分 | 點擊「🚀 開始 7 分鐘學習衝刺」→ 完成答題 |
| 查看個人排行榜 | 點擊「排行榜」標籤 |
| 查看分行對戰 | 點擊「分行」標籤 |
| 查看歷史紀錄 | 點擊「歷史」標籤（需先模擬結算） |
| 開發測試工具 | 點擊左下角 🛠️ 圖示 |

---

## 🛠️ 開發測試面板說明

點擊畫面左下角的 **🛠️** 按鈕可以展開測試面板，功能說明如下：

| 按鈕 | 功能 |
|------|------|
| 重新載入預設狀態 | 清除所有資料，重新植入 40 位測試業務員的模擬資料 |
| 模擬每週日結算 | 產生下一週的新紀錄（積分歸零），舊資料變成歷史紀錄 |
| 快速加分（模組完成 +10） | 為目前登入的業務員直接加 10 分 |
| 快速加分（測驗全對 +5） | 額外加 5 分 |
| 快速加分（連續學習 +2） | 額外加 2 分 |
| 增加連勝天數 | 模擬「今天學習」，增加一天連勝 |
| 中斷連勝（缺課） | 模擬缺課，扣盾或斷連勝 |

---

## 主要 API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| `POST` | `/api/learning/complete-session` | 完成學習，寫入積分 |
| `GET` | `/api/learning/status/{agent_id}` | 查詢連勝與盾牌狀態 |
| `GET` | `/api/learning/history/{agent_id}` | 查詢歷史週積分 |
| `GET` | `/api/leaderboard/relative/{agent_id}` | 查詢個人相對排名 |
| `GET` | `/api/leaderboard/branch` | 查詢分行對戰排名 |
| `POST` | `/api/dev/seed` | 重新植入測試資料 |
| `POST` | `/api/dev/weekly-settlement` | 模擬週結算 |

> 完整 API 文件請訪問：http://localhost:8000/docs

---

## 技術架構

| 層 | 技術 | 版本 |
|----|------|------|
| 前端框架 | React | 19.x |
| 前端打包 | Vite | 8.x |
| 前端 HTTP | Axios | 1.x |
| 後端框架 | FastAPI | 0.115+ |
| ASGI 伺服器 | Uvicorn | 0.30+ |
| ORM | SQLAlchemy | 2.0+ |
| 資料庫 | PostgreSQL（正式）/ SQLite（DEMO） | — |
| 排程器 | APScheduler | 4.0.0a6（alpha） |
| 資料驗證 | Pydantic | v2 (2.10+) |
| 執行環境（後端） | Python | 3.10+（測試於 3.13.3） |
| 執行環境（前端） | Node.js | 18+（測試於 24.x） |

---

## 🐍 虛擬環境說明

本專案後端使用 Python 虛擬環境（`.venv`）確保跨電腦版本一致性。

```
life_pulse_backend/
├── .venv/          ← 虛擬環境目錄（已列入 .gitignore，不上傳）
├── requirements.txt ← 所有套件的版本約束
└── ...
```

> **為什麼需要 `--pre` 旗標？**  
> APScheduler 4.x 目前仍為 alpha 預覽版（`4.0.0a6`），PyPI 預設只安裝 stable release。  
> 加上 `--pre` 才能安裝到 4.x 版本。若使用一般 `pip install -r requirements.txt` 會安裝到 3.x，導致 `AsyncScheduler` 找不到的錯誤。

> **前端版本管理**：前端使用 `package-lock.json` 鎖定確切版本，執行 `npm install` 即可重現完全相同的依賴樹。
