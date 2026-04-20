"""
database.py — L.I.F.E. Pulse 資料庫引擎與連線池管理

支援雙模式運作：
- 正式模式：讀取 .env 中的 DATABASE_URL 連接 PostgreSQL
- DEMO 模式：若 .env 不存在或未設定，自動使用本地 SQLite（demo.db）
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# ── 決定使用 PostgreSQL 或 SQLite ──────────────────────────────────
if DATABASE_URL:
    # 正式模式：PostgreSQL
    if "localhost" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("localhost", "127.0.0.1")
    IS_SQLITE = False
    print("🐘 使用 PostgreSQL 資料庫")
else:
    # DEMO 模式：SQLite（不需任何安裝，零配置）
    _db_path = os.path.join(os.path.dirname(__file__), "demo.db")
    DATABASE_URL = f"sqlite:///{_db_path}"
    IS_SQLITE = True
    print(f"💡 未偵測到 DATABASE_URL，使用 SQLite DEMO 模式：{_db_path}")

# ── 建立資料庫引擎 ─────────────────────────────────────────────────
if IS_SQLITE:
    # SQLite 不支援連線池參數，使用 StaticPool 確保單執行緒安全
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=30,
        pool_recycle=3600,
        pool_timeout=30,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    FastAPI 依賴注入函數 (Dependency Injection)。
    每個 API 請求都會取得獨立的 DB Session，並在結束後確保釋放。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
