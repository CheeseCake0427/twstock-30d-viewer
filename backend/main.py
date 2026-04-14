import asyncio
import os
import signal
import time
from contextlib import asynccontextmanager

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import IDLE_SHUTDOWN_MINUTES
from data_fetcher import fetch_stock_data
from data_processor import process_stock_data
from ai_analyzer import generate_analysis

# 本地閒置自動關閉：追蹤最後請求時間
_last_request_time = time.time()


async def _idle_watcher():
    """背景檢查閒置時間，超過閾值就送 SIGINT 讓服務正常關閉。"""
    timeout = IDLE_SHUTDOWN_MINUTES * 60
    check_interval = min(30, timeout // 2)  # 每 30 秒檢查一次
    while True:
        await asyncio.sleep(check_interval)
        idle = time.time() - _last_request_time
        if idle >= timeout:
            print(
                f"[idle-shutdown] 閒置 {idle / 60:.1f} 分鐘 "
                f"(閾值 {IDLE_SHUTDOWN_MINUTES} 分鐘)，自動關閉服務"
            )
            os.kill(os.getpid(), signal.SIGINT)
            return


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = None
    if IDLE_SHUTDOWN_MINUTES > 0:
        print(
            f"[idle-shutdown] 已啟用：閒置 {IDLE_SHUTDOWN_MINUTES} 分鐘後自動關閉"
        )
        task = asyncio.create_task(_idle_watcher())
    yield
    if task:
        task.cancel()


app = FastAPI(title="台股分析系統", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _track_activity(request: Request, call_next):
    """每次收到請求就更新 last_request_time。"""
    global _last_request_time
    _last_request_time = time.time()
    return await call_next(request)


@app.get("/api/stock/{code}")
def get_stock(code: str):
    raw = fetch_stock_data(code)
    result = process_stock_data(raw)

    # 如果有 error 欄位，代表查無資料
    if "error" in result:
        return {
            "stock": {"code": code, "name": ""},
            "data": [],
            "analysis": None,
            "warnings": [],
            "extra": None,
            "error": result["error"],
        }

    # AI 分析（事實提取 + 文字生成）
    analysis = generate_analysis(result["data"], result["warnings"], result.get("raw_count", 0))

    # 清除內部欄位，不回傳給前端
    clean_data = [
        {k: v for k, v in d.items() if not k.startswith("_")}
        for d in result["data"]
    ]

    return {
        "stock": result["stock"],
        "data": clean_data,
        "analysis": analysis,
        "warnings": result["warnings"],
        "extra": None,  # Phase 5 實作
    }
