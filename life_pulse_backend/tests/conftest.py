"""
tests/conftest.py — pytest 測試環境設定

策略：使用 SQLite in-memory 資料庫取代 PostgreSQL。
關鍵修正：API 路由的 get_db() 與測試查詢必須共用「同一個 Session 物件」，
  否則 SQLite 的連線隔離會導致 API 寫入後，測試側看不到資料。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """
    每個測試函數獲得乾淨的 Session。
    測試開始前建表、結束後 drop，確保完全隔離。
    """
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db):
    """
    FastAPI TestClient，將 get_db 覆寫為與 db fixture 完全相同的 Session。

    重要：override 必須 yield 同一個 session 實例（而非新開），
    這樣 API 寫入的資料才能在同一個交易內被測試程式查詢到。
    """
    def override_get_db():
        yield db  # 直接 yield 同一個 session 物件

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
