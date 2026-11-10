# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

import pymysql
import pytest
from pymysql.cursors import DictCursor

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SEED_SQL = ROOT / "00_test_seed.sql"


def _load_dotenv():
    """读取 functional_tests/.env（可选），方便本地配置数据库密码。"""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

from browser import BASE_URL, create_driver  # noqa: E402

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USERNAME", "train_app")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "train_ticket")


def _connect():
    if not DB_PASSWORD:
        raise RuntimeError(
            "缺少 DB_PASSWORD：请创建 functional_tests/.env 并填写，"
            "或先设置环境变量 DB_PASSWORD（不要提交 .env）"
        )
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, charset="utf8mb4", cursorclass=DictCursor,
        autocommit=True,
    )


@pytest.fixture(scope="session", autouse=True)
def seed_data():
    """套件开始前重置功能测试专用车次/座位/测试用户。"""
    sql = SEED_SQL.read_text(encoding="utf-8")
    statements = []
    for chunk in sql.split(";"):
        lines = [line for line in chunk.splitlines() if not line.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if stmt:
            statements.append(stmt)
    try:
        conn = _connect()
    except Exception as e:
        raise RuntimeError(
            f"连接 MySQL 失败（{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}）：{e}；"
            "请确认 8080 应用使用的是 MySQL，并先执行 db/01_schema.sql、02_seed.sql"
        ) from e
    try:
        with conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)
    finally:
        conn.close()


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def driver(seed_data):
    d = create_driver()
    yield d
    try:
        d.quit()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def fresh_session(driver):
    """每条用例开始前清 Cookie，保证未登录/登录场景互不影响。"""
    try:
        driver.delete_all_cookies()
    except Exception:
        pass
    yield


@pytest.fixture(scope="session")
def db():
    conn = _connect()
    yield conn
    conn.close()
