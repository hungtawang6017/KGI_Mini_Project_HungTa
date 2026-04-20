# 🐍 L.I.F.E. Pulse — 後端 API 說明

> FastAPI + SQLAlchemy 後端服務，負責積分計算、連勝判定、排行榜管理。

---

## 📁 檔案結構地圖

```
life_pulse_backend/
│
├── main.py              ← 🚀 伺服器啟動入口（FastAPI App + CORS + APScheduler）
├── database.py          ← 🗄️ 資料庫引擎（自動偵測 PostgreSQL / SQLite）
├── models.py            ← 📋 資料庫資料表 ORM 定義（三張表）
├── schemas.py           ← 📐 API 資料格式驗證（Pydantic v2）
├── crud.py              ← ⚙️ 核心業務邏輯（積分、連勝、排行榜運算）
├── seed_data.py         ← 🌱 測試資料植入腳本
│
├── routers/             ← API 路由模組（每個檔案對應一組 API）
│   ├── learning.py      ← POST /api/learning/...（完成學習、查狀態、查歷史）
│   ├── leaderboard.py   ← GET  /api/leaderboard/...（排行榜）
│   ├── streak.py        ← POST /api/streak/...（每日連勝結算）
│   └── dev.py           ← POST /api/dev/...（🛠️ 開發測試專用）
│
├── tests/               ← 自動化測試（pytest）
│
├── requirements.txt     ← Python 套件清單
├── .env.example         ← 環境變數範本（複製為 .env 使用）
├── .env                 ← 🔒 實際環境設定（勿上傳 Git！）
└── .gitignore
```

---

## 🗄️ 資料庫三表設計詳解

### 表 1：`PointLedger`（積分帳本）

**設計理念**：純 Append-only，所有積分事件只增不改，確保稽核可追溯性。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `transaction_id` | INT (PK) | 自動遞增，唯一交易 ID |
| `agent_id` | VARCHAR | 業務員 ID |
| `event_type` | VARCHAR | 事件類型（如 `course_completion`、`quiz_perfect_bonus`） |
| `points_awarded` | INT | 本次獲得的積分 |
| `created_at` | TIMESTAMP | 事件發生時間（自動填入） |

---

### 表 2：`AgentStreaks`（連勝狀態機）

**設計理念**：每位業務員只有一筆紀錄，每日更新，記錄當前的連勝與盾牌狀態。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `streak_id` | INT (PK) | 自動遞增 |
| `agent_id` | VARCHAR (UNIQUE) | 每人只有一筆 |
| `current_streak_days` | INT | 當前連續學習天數（🔥 火焰數字） |
| `longest_historical_streak` | INT | 歷史最長連勝（不隨斷連消失） |
| `active_shields_count` | INT | 當前持有防護罩數量（🛡️） |
| `last_study_date` | DATE | 最後學習日期（每日結算時比對） |

---

### 表 3：`LeaderboardStandings`（週排行榜 + 歷史存檔）

**設計理念**：透過 `epoch_week_number` 區分「本週」與「歷史」，一張表同時服務兩種需求。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `standing_id` | INT (PK) | 自動遞增 |
| `agent_id` | VARCHAR | 業務員 ID |
| `branch_id` | VARCHAR | 所屬分公司（用於分行對戰） |
| `epoch_week_number` | VARCHAR | 週次識別碼，格式 `YYYYWW`（如 `202616`） |
| `weekly_points_total` | INT | 該週累計積分 |

> **本週 vs 歷史的判斷邏輯**：查詢時抓出資料庫中**最大的 epoch_week_number**作為「當前週」，其餘皆為歷史紀錄。

---

## 🚀 安裝與啟動步驟

### 前置需求

- Python 3.10 以上版本
- PostgreSQL（選用，沒有的話系統自動使用 SQLite）

---

### Step 1：安裝套件

```bash
# 在 life_pulse_backend 目錄下執行
pip install -r requirements.txt
```

**requirements.txt 包含的套件：**
| 套件 | 用途 |
|------|------|
| `fastapi` | Web 框架，定義 API |
| `uvicorn` | ASGI 伺服器，啟動 FastAPI |
| `sqlalchemy` | ORM，操作資料庫 |
| `psycopg2-binary` | PostgreSQL 驅動（若使用 SQLite 可不安裝） |
| `python-dotenv` | 讀取 `.env` 環境變數 |
| `pydantic` | 資料格式驗證 |
| `apscheduler` | 每日自動定時結算 |

---

### Step 2：設定資料庫

#### 選項 A：使用 PostgreSQL（正式模式）

```bash
# 1. 複製範本檔案
cp .env.example .env

# 2. 編輯 .env，填入你的連線資訊
# DATABASE_URL=postgresql+psycopg2://帳號:密碼@localhost:5432/life_pulse_db
```

**PostgreSQL 資料庫建立範例：**
```sql
CREATE DATABASE life_pulse_db;
CREATE USER life_pulse_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE life_pulse_db TO life_pulse_user;
```

#### 選項 B：不使用資料庫（DEMO 模式）

> 完全不需要做任何設定！只要不建立 `.env` 檔案，系統就會自動在目錄下建立 `demo.db`（SQLite）。

---

### Step 3：植入測試資料

```bash
python seed_data.py
```

執行後會：
1. 刪除並重建所有資料表（確保 Schema 為最新版本）
2. 植入 40 位模擬業務員的學習資料
3. 植入過去 2 週的歷史積分（供「歷史紀錄」標籤測試使用）

**植入後可以登入的帳號：**
```
tester_01
agent_ruiguang_01 ~ agent_ruiguang_40
```

---

### Step 4：啟動伺服器

```bash
uvicorn main:app --reload
```

- `--reload`：開發模式，修改程式碼後自動重啟
- 預設監聽 `http://localhost:8000`

**啟動成功的訊息：**
```
💡 未偵測到 DATABASE_URL，使用 SQLite DEMO 模式  ← SQLite 模式
🐘 使用 PostgreSQL 資料庫                        ← PostgreSQL 模式
⏰ APScheduler 4.x 啟動，每日 00:01 自動執行連勝結算
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## 📡 完整 API 端點說明

### 學習引擎（`/api/learning/`）

#### `POST /api/learning/complete-session`
**功能**：業務員完成一次學習衝刺，寫入積分並更新連勝狀態。

**請求 Body：**
```json
{
  "agent_id": "tester_01",
  "event_type": "course_completion",
  "is_quiz_perfect": false
}
```

**回傳：**
```json
{
  "success": true,
  "transaction_id": 856,
  "points_awarded": 12,
  "streak": {
    "current_streak_days": 3,
    "longest_historical_streak": 5,
    "active_shields_count": 1,
    "has_studied_today": true,
    "shield_awarded": true
  }
}
```

**積分計算規則：**
- 完成學習：+10 分
- 測驗全對：+5 分（額外）
- 連續學習：+2 分（額外）

---

#### `GET /api/learning/status/{agent_id}`
**功能**：查詢業務員當前的連勝天數、盾牌數量。

**回傳：**
```json
{
  "current_streak_days": 5,
  "longest_historical_streak": 12,
  "active_shields_count": 1,
  "has_studied_today": true,
  "shield_awarded": false
}
```

---

#### `GET /api/learning/history/{agent_id}`
**功能**：查詢業務員過去每週的積分紀錄（週結算後才會出現）。

**回傳：**
```json
[
  { "epoch_week_number": "202615", "final_points": 45 },
  { "epoch_week_number": "202614", "final_points": 72 }
]
```

---

### 排行榜（`/api/leaderboard/`）

#### `GET /api/leaderboard/relative/{agent_id}`
**功能**：以指定業務員為中心，顯示其前後 2 名的相對排名（隱私保護設計：其他人的 ID 被匿名化）。

---

#### `GET /api/leaderboard/branch`
**功能**：取得各分公司的本週積分加總排名。

---

### 開發測試（`/api/dev/`，🛠️ 僅開發環境使用）

| 端點 | 說明 |
|------|------|
| `POST /api/dev/seed` | 重新植入測試資料（清除舊資料） |
| `POST /api/dev/weekly-settlement` | 模擬週結算（產生下週紀錄，積分歸零） |
| `POST /api/dev/simulate-settlement` | 模擬每日結算（連勝判定） |
| `POST /api/dev/increase-streak/{agent_id}` | 增加連勝天數 |
| `POST /api/dev/break-streak/{agent_id}` | 中斷連勝（模擬缺課） |
| `POST /api/dev/award-bonus/{agent_id}` | 直接加分（指定事件類型） |

---

## ⚙️ 核心邏輯說明（crud.py）

### 每日結算流程（`run_daily_settlement`）

```
針對每位業務員執行以下判斷：
    if 今天有學習:
        → 跳過（連勝正常）
    else:
        if 有防護罩:
            → 扣除 1 面防護罩，連勝天數保留
        else:
            → 連勝天數歸零
```

### 週結算流程（`perform_weekly_settlement`）

```
1. 找到資料庫中最新的週次（例如 202616）
2. 計算下一週（202617）
3. 為所有人在 LeaderboardStandings 新增一筆該週的空紀錄（積分=0）
4. 舊紀錄自然成為歷史資料
```

---

## 🔒 安全設計原則

1. **Append-only 積分帳本**：`PointLedger` 只能新增，永不修改或刪除
2. **隱私排行榜**：其他業務員的 ID 透過單向雜湊匿名化，無法反推
3. **冪等性保護**：同一天重複呼叫 `complete-session` 不會重複計算連勝
4. **機敏資料隔離**：資料庫密碼存於 `.env`，已列入 `.gitignore`
