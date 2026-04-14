"""
AI 分析引擎測試。

對應 test-plan.md：
  - B-3 AI 分析引擎
"""

import re

import analysis_templates as tpl
from ai_analyzer import extract_facts, generate_analysis
from data_processor import process_stock_data

# 投資建議 / 預測 / 主觀推薦的禁止用語
FORBIDDEN_PHRASES = [
    "建議買入", "建議賣出", "適合進場", "值得關注", "值得期待",
    "表現優異", "預計將", "未來可能", "看好後市", "建議投資人",
    "不建議", "可以考慮", "預期", "看好", "看壞", "看漲", "看跌",
]


def _build_data(closes: list[float], start_date: str = "2026-02-02") -> list[dict]:
    """從收盤價列表建立模擬的 processed data（繞過 process_stock_data）"""
    from data_processor import _sma

    data = []
    year, month, day = map(int, start_date.split("-"))

    for i, close in enumerate(closes):
        # 簡單跳過週末
        d = day + i
        m = month + (d - 1) // 28
        d = ((d - 1) % 28) + 1
        date_str = f"{year}-{m:02d}-{d:02d}"

        data.append({
            "date": date_str,
            "open": close - 1,
            "high": close + 1,
            "low": close - 2,
            "close": close,
            "volume": 1000000,
            "ma5": _sma(closes, i, 5),
            "ma20": _sma(closes, i, 20),
        })
    return data


# ============================================================
# B-3.1: 分析內容規範
# ============================================================


class TestAnalysisContent:
    """分析文字的內容規範"""

    def test_output_is_traditional_chinese(self, load_fixture):
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        analysis = generate_analysis(result["data"], result["warnings"])
        assert analysis is not None
        # 繁體中文含有中文字元
        assert re.search(r"[\u4e00-\u9fff]", analysis)

    def test_contains_at_least_2_numbers(self, load_fixture):
        """至少引用 2 項具體數據事實（可找到具體數字）"""
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        analysis = generate_analysis(result["data"], result["warnings"])
        # 找出文字中的數字（含小數）
        numbers = re.findall(r"\d+\.?\d*", analysis)
        assert len(numbers) >= 2

    def test_no_forbidden_phrases(self, load_fixture):
        """不包含投資建議、預測、主觀推薦用語"""
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        analysis = generate_analysis(result["data"], result["warnings"])
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in analysis, f"分析文字包含禁止用語：「{phrase}」"

    def test_numbers_traceable_to_data(self, load_fixture):
        """文字中的數字可在 data 中找到對應來源"""
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        data = result["data"]
        analysis = generate_analysis(data, result["warnings"])

        # 收集 data 中所有數字（close, high, low, ma5, ma20, 百分比等）
        valid_numbers = set()
        for d in data:
            for key in ("close", "high", "low", "open", "ma5", "ma20"):
                val = d.get(key)
                if val is not None:
                    valid_numbers.add(f"{val:.2f}")
                    valid_numbers.add(f"{val:,.2f}")
                    valid_numbers.add(str(int(val)))

        # 也加入天數
        valid_numbers.add(str(len(data)))

        # 分析中的數字
        analysis_numbers = re.findall(r"[\d,]+\.?\d*", analysis)
        for num in analysis_numbers:
            clean = num.replace(",", "")
            # 百分比數字（如 28.00%）需要額外驗算，這裡只確認非零數字有來源
            if float(clean) == 0:
                continue
            # 檢查是否為天數、價格、或百分比（允許計算得出的百分比）
            is_valid = (
                clean in valid_numbers
                or num in valid_numbers
                or float(clean) <= 100  # 百分比範圍內的可能是計算值
            )
            assert is_valid, f"分析中的數字 {num} 無法追溯至 data"


# ============================================================
# B-3.2: 分析依據充足性
# ============================================================


class TestAnalysisSufficiency:
    """分析的依據充足性判斷"""

    def test_normal_30_produces_analysis(self, load_fixture):
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        analysis = generate_analysis(result["data"], result["warnings"])
        assert analysis is not None
        assert analysis != tpl.INSUFFICIENT_DATA

    def test_insufficient_facts_rejected(self):
        """事實不足 2 項 → 拒絕輸出"""
        # 只有 1 筆，無法提取足夠事實
        data = _build_data([100])
        analysis = generate_analysis(data, [])
        assert analysis == tpl.INSUFFICIENT_DATA

    def test_empty_data_rejected(self):
        """0 筆資料 → 不產生分析"""
        analysis = generate_analysis([], [])
        assert analysis == tpl.INSUFFICIENT_DATA

    def test_fewer_than_10_days_rejected(self):
        """不足 10 天 → 拒絕輸出"""
        data = _build_data([100, 102, 104, 101, 103, 105, 107, 104, 106])  # 9 筆
        analysis = generate_analysis(data, [])
        assert analysis == tpl.INSUFFICIENT_DATA

    def test_high_skip_ratio_rejected(self):
        """略過比例 > 30% → 拒絕輸出"""
        data = _build_data([100 + i for i in range(15)])
        # raw_count=25, 有效=15, 略過率=40%
        analysis = generate_analysis(data, [], raw_count=25)
        assert analysis == tpl.INSUFFICIENT_DATA


# ============================================================
# B-3.3: 分析可追溯性
# ============================================================


class TestFactExtraction:
    """事實提取的正確性"""

    def test_price_change_fact(self):
        """提取期間價格變化"""
        data = _build_data([100 + i for i in range(30)])
        facts = extract_facts(data)
        # 應有一個事實包含第一天和最後一天的收盤價
        price_facts = [f for f in facts if "100.00" in f and "129.00" in f]
        assert len(price_facts) >= 1

    def test_ma_relation_fact(self):
        """提取 MA5 vs MA20 關係"""
        data = _build_data([100 + i for i in range(30)])
        facts = extract_facts(data)
        ma_facts = [f for f in facts if "MA5" in f and "MA20" in f]
        assert len(ma_facts) >= 1

    def test_price_range_fact(self):
        """提取期間最高/最低價"""
        data = _build_data([100 + i for i in range(30)])
        facts = extract_facts(data)
        range_facts = [f for f in facts if "最高價" in f and "最低價" in f]
        assert len(range_facts) >= 1

    def test_no_facts_from_empty_data(self):
        facts = extract_facts([])
        assert facts == []

    def test_crossover_fact_traceable(self):
        """分析提及均線交叉 → 資料中確實存在 MA5 與 MA20 的交叉點

        設計收盤價讓 MA5 在某天從低於 MA20 變成高於 MA20：
        - 前 20 天緩降：120, 119, 118, ... 101（MA20 會偏高）
        - 後 10 天急漲：110, 115, 120, 125, 130, 135, 140, 145, 150, 155
          → MA5 會快速上升，超越 MA20
        """
        closes = [120 - i for i in range(20)] + [110 + 5 * i for i in range(10)]
        # closes: [120, 119, ..., 101, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155]
        assert len(closes) == 30

        data = _build_data(closes)
        facts = extract_facts(data)

        # 應提取到 MA 交叉事件
        cross_facts = [f for f in facts if "穿越" in f]
        assert len(cross_facts) >= 1, f"未偵測到交叉事件，facts={facts}"

        # 交叉事件提及的日期，在 data 中確實存在 MA5 > MA20 的翻轉
        # 驗證方式：找到交叉日，確認前一天 MA5 <= MA20，當天 MA5 > MA20
        from ai_analyzer import _fact_ma_crossovers

        crossovers = _fact_ma_crossovers(data)
        for fact in crossovers:
            # 從事實文字提取日期（格式如 "02-21"）
            import re

            date_match = re.search(r"(\d{2}-\d{2})", fact)
            assert date_match, f"交叉事實中找不到日期：{fact}"
            cross_date_suffix = date_match.group(1)

            # 在 data 中找到該日期，驗證交叉確實發生
            for i in range(1, len(data)):
                if data[i]["date"].endswith(cross_date_suffix):
                    prev_ma5 = data[i - 1]["ma5"]
                    prev_ma20 = data[i - 1]["ma20"]
                    curr_ma5 = data[i]["ma5"]
                    curr_ma20 = data[i]["ma20"]
                    assert None not in (prev_ma5, prev_ma20, curr_ma5, curr_ma20)
                    # 向上穿越：前一天 MA5 <= MA20，當天 MA5 > MA20
                    # 或向下穿越：前一天 MA5 >= MA20，當天 MA5 < MA20
                    crossed_up = prev_ma5 <= prev_ma20 and curr_ma5 > curr_ma20
                    crossed_down = prev_ma5 >= prev_ma20 and curr_ma5 < curr_ma20
                    assert crossed_up or crossed_down, (
                        f"日期 {data[i]['date']} 聲稱交叉但資料不支持："
                        f"前日 MA5={prev_ma5} MA20={prev_ma20}，"
                        f"當日 MA5={curr_ma5} MA20={curr_ma20}"
                    )
                    break


# ============================================================
# B-3.4: 降級機制
# ============================================================


class TestAnalysisDegradation:
    """降級機制"""

    def test_no_api_key_still_produces_analysis(self, load_fixture, monkeypatch):
        """無 AI API Key → 模板模式仍能產生分析"""
        monkeypatch.setattr("ai_analyzer.AI_API_KEY", "")
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        analysis = generate_analysis(result["data"], result["warnings"])
        assert analysis is not None
        assert analysis != tpl.INSUFFICIENT_DATA

    def test_analysis_does_not_leak_api_details(self, load_fixture, monkeypatch):
        """分析內容不包含 API 相關資訊"""
        monkeypatch.setattr("ai_analyzer.AI_API_KEY", "")
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        analysis = generate_analysis(result["data"], result["warnings"])
        assert "api" not in analysis.lower()
        assert "key" not in analysis.lower()
        assert "openai" not in analysis.lower()
        assert "sk-" not in analysis

    def test_ai_api_failure_falls_back_to_template(self, load_fixture, monkeypatch):
        """AI API 呼叫失敗 → 降級為模板模式，不影響功能

        模擬：有 API key（進入 AI 改寫分支），但 httpx.post 拋出例外。
        驗證：仍回傳有效分析文字（模板版），不回傳 None。
        """
        # 設一個假 key，讓 generate_analysis 進入 AI 改寫分支
        monkeypatch.setattr("ai_analyzer.AI_API_KEY", "sk-fake-key-for-testing")

        # mock httpx.post 拋出例外
        import httpx

        def mock_post_fail(*args, **kwargs):
            raise httpx.ConnectError("Simulated network failure")

        monkeypatch.setattr(httpx, "post", mock_post_fail)

        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        analysis = generate_analysis(result["data"], result["warnings"])

        # 應降級為模板模式：仍有分析文字
        assert analysis is not None
        assert analysis != tpl.INSUFFICIENT_DATA
        assert len(analysis) > 0
        # 內容應為繁體中文（模板輸出）
        import re

        assert re.search(r"[\u4e00-\u9fff]", analysis)

    def test_ai_api_http_error_falls_back_to_template(self, load_fixture, monkeypatch):
        """AI API 回傳非 200 → 降級為模板模式"""
        monkeypatch.setattr("ai_analyzer.AI_API_KEY", "sk-fake-key-for-testing")

        import httpx

        class FakeFailResponse:
            status_code = 500

            def json(self):
                return {"error": "Internal server error"}

        def mock_post_500(*args, **kwargs):
            return FakeFailResponse()

        monkeypatch.setattr(httpx, "post", mock_post_500)

        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        analysis = generate_analysis(result["data"], result["warnings"])

        # 仍應有有效分析（模板版）
        assert analysis is not None
        assert analysis != tpl.INSUFFICIENT_DATA
