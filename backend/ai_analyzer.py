"""AI 分析層：事實提取 + 文字生成（模板模式 / AI 改寫模式）"""

import re

import analysis_templates as tpl
from config import AI_API_KEY


def generate_analysis(data: list[dict], warnings: list[str], raw_count: int = 0) -> str | None:
    """產生分析文字。資料不足時回傳 None。

    Args:
        data: L2 處理後的結構化資料列表（含 date, close, ma5, ma20 等）
        warnings: L2 產生的 warnings 列表
        raw_count: 清洗前的原始資料筆數，用於計算略過比例
    """
    # P1: 資料天數不足 10 → 拒絕輸出
    if len(data) < 10:
        return tpl.INSUFFICIENT_DATA

    # P1: 被略過比例 > 30% → 拒絕輸出
    if raw_count > 0 and (raw_count - len(data)) / raw_count > 0.3:
        return tpl.INSUFFICIENT_DATA

    # --- 第一層：事實提取 ---
    facts = extract_facts(data)

    # 事實不足 2 項 → 拒絕輸出
    if len(facts) < 2:
        return tpl.INSUFFICIENT_DATA

    # --- 第二層：文字生成 ---
    ai_key = AI_API_KEY.strip()

    if ai_key:
        ai_result = _ai_rewrite(facts, ai_key)
        if ai_result:
            return ai_result
        # AI 失敗 → 降級為模板模式

    return _template_render(facts, len(data))


def extract_facts(data: list[dict]) -> list[str]:
    """從結構化資料中提取可被數據直接佐證的事實。"""
    if not data:
        return []

    facts = []

    # 1. 期間價格變化
    fact = _fact_price_change(data)
    if fact:
        facts.append(fact)

    # 2. MA5 vs MA20 關係（取最後一筆）
    fact = _fact_ma_relation(data)
    if fact:
        facts.append(fact)

    # 3. 期間最高/最低價
    fact = _fact_price_range(data)
    if fact:
        facts.append(fact)

    # 4. MA 交叉事件
    cross_facts = _fact_ma_crossovers(data)
    facts.extend(cross_facts)

    # 5. 近期趨勢（近 5 日）
    fact = _fact_recent_trend(data)
    if fact:
        facts.append(fact)

    return facts


# --- 事實提取函式 ---


def _fact_price_change(data: list[dict]) -> str | None:
    first_close = data[0]["close"]
    last_close = data[-1]["close"]
    if first_close <= 0 or last_close <= 0:
        return None

    change_pct = abs((last_close - first_close) / first_close * 100)
    change_pct_str = f"{change_pct:.2f}"
    first_str = f"{first_close:,.2f}"
    last_str = f"{last_close:,.2f}"

    if last_close > first_close:
        return tpl.PRICE_CHANGE_UP.format(
            start_price=first_str, end_price=last_str, change_pct=change_pct_str
        )
    elif last_close < first_close:
        return tpl.PRICE_CHANGE_DOWN.format(
            start_price=first_str, end_price=last_str, change_pct=change_pct_str
        )
    else:
        return tpl.PRICE_CHANGE_FLAT.format(
            start_price=first_str, end_price=last_str, change_pct=change_pct_str
        )


def _fact_ma_relation(data: list[dict]) -> str | None:
    last = data[-1]
    ma5 = last.get("ma5")
    ma20 = last.get("ma20")
    if ma5 is None or ma20 is None:
        return None

    ma5_str = f"{ma5:,.2f}"
    ma20_str = f"{ma20:,.2f}"

    if ma5 > ma20:
        return tpl.MA_RELATION_ABOVE.format(ma5=ma5_str, ma20=ma20_str)
    elif ma5 < ma20:
        return tpl.MA_RELATION_BELOW.format(ma5=ma5_str, ma20=ma20_str)
    else:
        return tpl.MA_RELATION_EQUAL.format(ma5=ma5_str, ma20=ma20_str)


def _fact_price_range(data: list[dict]) -> str | None:
    valid = [d for d in data if d["close"] > 0]
    if not valid:
        return None

    valid_high = [d for d in valid if d["high"] > 0]
    valid_low = [d for d in valid if d["low"] > 0]
    if not valid_high or not valid_low:
        return None

    high_day = max(valid_high, key=lambda d: d["high"])
    low_day = min(valid_low, key=lambda d: d["low"])

    return tpl.PRICE_RANGE.format(
        high_price=f"{high_day['high']:,.2f}",
        high_date=high_day["date"][5:],  # "2026-03-02" → "03-02"
        low_price=f"{low_day['low']:,.2f}",
        low_date=low_day["date"][5:],
    )


def _fact_ma_crossovers(data: list[dict]) -> list[str]:
    """偵測 MA5 與 MA20 的交叉事件。"""
    facts = []

    for i in range(1, len(data)):
        prev_ma5 = data[i - 1].get("ma5")
        prev_ma20 = data[i - 1].get("ma20")
        curr_ma5 = data[i].get("ma5")
        curr_ma20 = data[i].get("ma20")

        if None in (prev_ma5, prev_ma20, curr_ma5, curr_ma20):
            continue

        date_str = data[i]["date"][5:]

        # 前一天 MA5 <= MA20，今天 MA5 > MA20 → 向上穿越
        if prev_ma5 <= prev_ma20 and curr_ma5 > curr_ma20:
            facts.append(tpl.MA_CROSS_UP.format(date=date_str))

        # 前一天 MA5 >= MA20，今天 MA5 < MA20 → 向下穿越
        elif prev_ma5 >= prev_ma20 and curr_ma5 < curr_ma20:
            facts.append(tpl.MA_CROSS_DOWN.format(date=date_str))

    return facts


def _fact_recent_trend(data: list[dict], n: int = 5) -> str | None:
    """判斷近 n 個交易日的收盤價趨勢。"""
    if len(data) < n:
        return None

    recent = data[-n:]
    closes = [d["close"] for d in recent]

    ups = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i - 1])
    downs = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i - 1])

    # P1: 淨變動方向必須與趨勢方向一致
    net_change = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0

    if ups >= n - 1 and net_change > 0:
        return tpl.TREND_UP.format(n=n)
    elif downs >= n - 1 and net_change < 0:
        return tpl.TREND_DOWN.format(n=n)
    # 不夠明確的趨勢不輸出，避免模糊描述
    return None


# --- 文字生成 ---


def _template_render(facts: list[str], days: int) -> str:
    """模板模式：將事實列表串接為段落。"""
    # 用句號連接各事實
    facts_text = "。".join(facts) + "。"
    return tpl.FULL_ANALYSIS.format(days=days, facts_text=facts_text)


def _ai_rewrite(facts: list[str], api_key: str) -> str | None:
    """AI 改寫模式：將事實列表交給 AI 改寫為流暢段落。失敗回傳 None。"""
    try:
        import httpx

        facts_list = "\n".join(f"- {f}" for f in facts)
        prompt = tpl.AI_REWRITE_PROMPT.format(facts_list=facts_list)

        # 嘗試 OpenAI 相容 API
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 500,
            },
            timeout=10,
        )

        if resp.status_code == 200:
            text = resp.json()["choices"][0]["message"]["content"].strip()
            if _validate_rewrite(text, facts):
                return text
            return None  # 驗證失敗 → fallback 到模板模式

        return None
    except Exception:
        return None


def _validate_rewrite(text: str, facts: list[str]) -> bool:
    """驗證 AI 改寫結果：數字未捏造 + 無禁用詞。"""
    # 禁用詞檢查
    for keyword in tpl.BANNED_KEYWORDS:
        if keyword in text:
            return False

    # 數字比對：LLM 輸出不得包含 facts 中不存在的數字
    facts_joined = " ".join(facts)
    facts_numbers = _extract_numbers(facts_joined)
    output_numbers = _extract_numbers(text)
    if output_numbers - facts_numbers:
        return False

    return True


def _extract_numbers(text: str) -> set[str]:
    """提取文字中所有數字，統一為去逗號、去尾零的格式。"""
    raw = re.findall(r"\d[\d,]*(?:\.\d+)?", text)
    normalized = set()
    for n in raw:
        clean = n.replace(",", "")
        # 有小數點的去尾零：1935.00 → 1935, 19.60 → 19.6, 19.61 → 19.61
        if "." in clean:
            clean = clean.rstrip("0").rstrip(".")
        normalized.add(clean)
    return normalized
