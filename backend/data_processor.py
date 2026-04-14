def process_stock_data(raw: dict) -> dict:
    """處理 TWSE 格式的原始資料，回傳結構化結果。

    回傳格式:
    {
        "stock": {"code": str, "name": str},
        "data": [{"date", "open", "high", "low", "close", "volume", "ma5", "ma20"}, ...],
        "warnings": [str, ...],
        "raw_count": int,
    }
    """
    warnings = []

    raw_count = len(raw.get("data", []))

    # --- 檢查 stat ---
    if raw.get("stat") != "OK" or "data" not in raw:
        return {
            "stock": {"code": "", "name": ""},
            "data": [],
            "warnings": [],
            "raw_count": 0,
            "error": raw.get("stat", "未知錯誤"),
        }

    # --- 解析 title 取得股票代號與名稱 ---
    code, name = _parse_title(raw.get("title", ""))

    # --- 清洗每一筆資料 ---
    cleaned = []
    for row in raw["data"]:
        parsed = _parse_row(row)
        if parsed is None:
            warnings.append(f"資料異常，已略過一筆：{row[0] if row else '未知'}")
            continue
        if parsed.get("_bad_close"):
            reason = parsed.get("_bad_close_reason", "異常")
            warnings.append(f"{parsed['date']} 收盤價{reason}，該筆不納入計算")
            continue
        if parsed.get("_bad_ohlc"):
            fields = "、".join(parsed["_bad_ohlc"])
            warnings.append(f"{parsed['date']} {fields}為空，圖表顯示可能異常")
        cleaned.append(parsed)

    # --- P0: 日期排序驗證 ---
    if len(cleaned) > 1:
        is_sorted = all(
            cleaned[i]["date"] > cleaned[i - 1]["date"]
            for i in range(1, len(cleaned))
        )
        if not is_sorted:
            cleaned.sort(key=lambda d: d["date"])
            warnings.append("資料日期順序異常，已自動重新排序")

    # --- P2: 單日漲跌幅異常檢查 ---
    for i in range(1, len(cleaned)):
        prev_close = cleaned[i - 1]["close"]
        curr_close = cleaned[i]["close"]
        if prev_close > 0:
            change_pct = (curr_close - prev_close) / prev_close * 100
            if abs(change_pct) > 50:
                warnings.append(
                    f"{cleaned[i]['date']} 價格波動異常（{change_pct:+.1f}%），請確認資料正確性"
                )

    # --- 截取最近 30 個交易日 ---
    if len(cleaned) > 30:
        cleaned = cleaned[-30:]

    total = len(cleaned)

    if total == 0:
        warnings.append("無有效交易日資料")
        return {"stock": {"code": code, "name": name}, "data": [], "warnings": warnings, "raw_count": raw_count}

    if total < 30:
        warnings.append(f"資料僅 {total} 個交易日，不足 30 日")

    # --- 計算 MA5 / MA20 ---
    closes = [d["close"] for d in cleaned]

    if total < 5:
        warnings.append("資料不足 5 筆，無法計算 MA5")
    if total < 20:
        warnings.append("資料不足 20 筆，無法計算 MA20")

    for i, d in enumerate(cleaned):
        d["ma5"] = _sma(closes, i, 5)
        d["ma20"] = _sma(closes, i, 20)

    return {
        "stock": {"code": code, "name": name},
        "data": cleaned,
        "warnings": warnings,
        "raw_count": raw_count,
    }


def _parse_title(title: str) -> tuple[str, str]:
    """從 TWSE title 解析代號與名稱。
    範例: '115年04月 2330 台積電       各日成交資訊'
    """
    parts = title.split()
    if len(parts) >= 3:
        return parts[1], parts[2]
    return "", ""


def _parse_row(row: list) -> dict | None:
    """將 TWSE data 陣列的一筆轉為 dict。"""
    if len(row) < 9:
        return None

    date_str = _roc_to_ad(row[0])
    if date_str is None:
        return None

    close_raw = row[6].replace(",", "").strip()
    empty_close = close_raw == ""
    close_val = _to_float(row[6]) if not empty_close else 0.0

    # P0: 收盤價非空但轉換後為 0 → 視為異常
    zero_close = (not empty_close) and close_val == 0.0
    # P2: 收盤價為負數 → 視為異常
    neg_close = close_val < 0

    # P1: 檢查 open/high/low 空值
    open_raw = row[3].replace(",", "").strip()
    high_raw = row[4].replace(",", "").strip()
    low_raw = row[5].replace(",", "").strip()
    bad_ohlc = []
    if open_raw == "" or open_raw == "--":
        bad_ohlc.append("開盤價")
    if high_raw == "" or high_raw == "--":
        bad_ohlc.append("最高價")
    if low_raw == "" or low_raw == "--":
        bad_ohlc.append("最低價")

    return {
        "date": date_str,
        "open": _to_float(row[3]),
        "high": _to_float(row[4]),
        "low": _to_float(row[5]),
        "close": close_val,
        "volume": _to_int(row[1]),
        "ma5": None,
        "ma20": None,
        "_bad_close": empty_close or zero_close or neg_close,
        "_bad_close_reason": "空" if empty_close else ("異常為 0" if zero_close else ("異常為負數" if neg_close else "")),
        "_bad_ohlc": bad_ohlc,
    }


def _roc_to_ad(roc_date: str) -> str | None:
    """民國曆轉西元。'115/04/01' → '2026-04-01'，'1150401' → '2026-04-01'"""
    s = roc_date.strip()
    if "/" in s:
        parts = s.split("/")
        if len(parts) != 3:
            return None
        try:
            year = int(parts[0]) + 1911
            return f"{year}-{parts[1]}-{parts[2]}"
        except ValueError:
            return None
    elif s.isdigit() and len(s) == 7:
        try:
            year = int(s[:3]) + 1911
            return f"{year}-{s[3:5]}-{s[5:7]}"
        except ValueError:
            return None
    return None


def _to_float(s: str) -> float:
    """移除逗號、處理正負號，轉為 float。"""
    s = s.replace(",", "").strip()
    if s.startswith("X"):
        s = s[1:]
    if s == "" or s == "--":
        return 0.0
    return float(s)


def _to_int(s: str) -> int:
    """移除逗號，轉為 int。"""
    s = s.replace(",", "").strip()
    if s == "" or s == "--":
        return 0
    return int(s)


def _sma(values: list[float], index: int, period: int) -> float | None:
    """計算簡單移動平均。index 為當前位置，period 為天數。"""
    if index < period - 1:
        return None
    window = values[index - period + 1 : index + 1]
    return round(sum(window) / period, 2)
