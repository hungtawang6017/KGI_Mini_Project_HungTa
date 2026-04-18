"""
database.py — L.I.F.E. Pulse 資料庫引擎與連線池管理

銀行級設計原則：
- 透過 python-dotenv 讀取 .env，確保機敏資料不寫入程式碼
- pool_pre_ping=True 自動偵測失效連線並重建，防範潛在斷線
- get_db() 依賴注入 + finally 區塊，確保 100% 安全釋放連線資源
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 從根目錄 .env 載入環境變數（機敏資料不寫入程式碼）
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ 環境變數 DATABASE_URL 未設定！請確認 .env 檔案存在且格式正確。")

# 建立資料庫引擎
# pool_pre_ping: 每次取用連線前先 ping 一次，避免使用到已失效的連線（防範 Connection Leak）
# pool_size: 連線池常駐連線數
# max_overflow: 高峰期可額外借用的臨時連線數
if DATABASE_URL and "localhost" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("localhost", "127.0.0.1")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,       # 增加連線池大小以應對並發
    max_overflow=30,    # 增加溢出連線
    pool_recycle=3600,  # 每小時回收連線
    pool_timeout=30,    # 等待連線超時時間
    echo=False,
)

# 建立 Session 工廠
# autocommit=False: 必須明確呼叫 commit()，確保交易原子性
# autoflush=False: 避免在 commit 前意外觸發資料庫寫入
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基底類別 — 所有 Model 都繼承自此
Base = declarative_base()


def get_db():
    """
    FastAPI 依賴注入函數 (Dependency Injection)。

    使用方式：在 API 路由函數的參數中加入 `db: Session = Depends(get_db)`

    設計保證：
    - 每個 API 請求都會取得獨立的 DB Session（並發安全）
    - 無論成功或發生任何異常，finally 區塊都會執行 db.close()
    - 防範連線池耗盡（Connection Pool Exhaustion）
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
