import json
import os
import time
from datetime import datetime

import requests

from config import DATA_SOURCE, SEED_DIR

# Seed 檔案中代號對應的檔名映射
_SEED_ALIAS = {
    "few": "stock_few.json",  # 測試資料不足情境
    "ohlc": "stock_ohlc_empty.json",  # 測試 open/high/low 空值
}

TWSE_URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
REQUEST_INTERVAL = 0.5  # 每次請求間隔秒數
REQUEST_TIMEOUT = 10


def fetch_stock_data(stock_no: str) -> dict:
    """取得股票原始資料。回傳 TWSE 格式的 dict（含 stat, data 等欄位）。"""
    if DATA_SOURCE == "seed":
        return _from_seed(stock_no)
    else:
        return _from_twse(stock_no)


def _from_seed(stock_no: str) -> dict:
    """從 seed 目錄讀取本地 JSON。"""
    filename = _SEED_ALIAS.get(stock_no, f"stock_{stock_no}.json")
    filepath = os.path.join(os.path.dirname(__file__), SEED_DIR, filename)

    if not os.path.exists(filepath):
        return {"stat": "很抱歉，沒有符合條件的資料!", "total": 0}

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _from_twse(stock_no: str) -> dict:
    """呼叫 TWSE 傳統 API，查詢當月 + 前 1~2 個月，合併資料。"""
    all_data = []
    title = ""
    now = datetime.now()

    for month_offset in range(3):  # 當月、前1月、前2月
        year = now.year
        month = now.month - month_offset
        if month <= 0:
            month += 12
            year -= 1
        date_str = f"{year}{month:02d}01"

        result = _fetch_one_month(stock_no, date_str)

        # 第一個月就失敗 → 代號無效或其他錯誤，直接回傳
        if result is None:
            if month_offset == 0:
                return {"stat": "資料來源暫時無法連線，請稍後再試", "total": 0}
            break

        if result.get("stat") != "OK" or "data" not in result:
            if month_offset == 0:
                return result  # 回傳 TWSE 原始錯誤訊息
            break

        # 保留 title（取最近月份的）
        if month_offset == 0:
            title = result.get("title", "")

        # 舊月份資料放前面
        all_data = result["data"] + all_data

        # 已經夠 30 筆以上就不再往前查
        if len(all_data) >= 30:
            break

        # 請求間隔
        if month_offset < 2:
            time.sleep(REQUEST_INTERVAL)

    if not all_data:
        return {"stat": "很抱歉，沒有符合條件的資料!", "total": 0}

    return {
        "stat": "OK",
        "title": title,
        "fields": ["日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價", "漲跌價差", "成交筆數"],
        "data": all_data,
        "total": len(all_data),
    }


def _fetch_one_month(stock_no: str, date: str) -> dict | None:
    """查詢 TWSE 單月資料。失敗回傳 None。"""
    try:
        resp = requests.get(
            TWSE_URL,
            params={"response": "json", "date": date, "stockNo": stock_no},
            timeout=REQUEST_TIMEOUT,
            verify=False,  # TWSE SSL 憑證在部分環境有問題
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.SSLError:
        # SSL 失敗時嘗試不驗證
        try:
            resp = requests.get(
                TWSE_URL,
                params={"response": "json", "date": date, "stockNo": stock_no},
                timeout=REQUEST_TIMEOUT,
                verify=False,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None
    except Exception:
        return None
