"""
資料取得層（網路行為）測試。

對應 test-plan.md：
  - B-4.5 資料來源異常（需 mock 網路）
  - B-5 資料來源切換

透過 monkeypatch 替換 requests.get，控制外部呼叫的行為。
"""

import requests

from data_fetcher import fetch_stock_data


# ============================================================
# 輔助工具
# ============================================================


class FakeResponse:
    """模擬 requests.Response 物件。"""

    def __init__(self, json_data=None, status_code=200, raise_on_json=False):
        self._json_data = json_data
        self.status_code = status_code
        self._raise_on_json = raise_on_json

    def json(self):
        if self._raise_on_json:
            raise ValueError("No JSON object could be decoded")
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code}")


def make_month_data(rows: int, month: str = "04", code: str = "2330"):
    """產生一個月的 TWSE 格式回應，指定筆數。"""
    data = []
    for i in range(1, rows + 1):
        data.append([
            f"115/{month}/{i:02d}",
            "1,000,000",
            "100,000,000",
            "100.00",
            "102.00",
            "99.00",
            "101.00",
            "+1.00",
            "1,000",
        ])
    return {
        "stat": "OK",
        "title": f"115年{month}月 {code} 測試股票各日成交資訊",
        "fields": ["日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價", "漲跌價差", "成交筆數"],
        "data": data,
        "total": rows,
    }


# ============================================================
# B-4.5: 資料來源異常
# ============================================================


class TestTwseConnectionFailure:
    """TWSE API 連線異常的處理。"""

    def test_timeout_returns_error_message(self, monkeypatch):
        """API 連線逾時 → 回傳使用者可理解的錯誤訊息"""
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "twse")

        def mock_get(*args, **kwargs):
            raise requests.exceptions.Timeout("Connection timed out")

        monkeypatch.setattr("data_fetcher.requests.get", mock_get)

        result = fetch_stock_data("2330")
        assert result.get("stat") != "OK"
        # 不應包含技術性 stack trace
        assert "Traceback" not in str(result)
        assert "Timeout" not in str(result.get("stat", ""))

    def test_non_json_response_no_crash(self, monkeypatch):
        """API 回傳非 JSON 格式 → 不 crash，回傳錯誤"""
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "twse")

        def mock_get(*args, **kwargs):
            return FakeResponse(raise_on_json=True)

        monkeypatch.setattr("data_fetcher.requests.get", mock_get)

        result = fetch_stock_data("2330")
        # 不應拋 exception，應正常回傳
        assert isinstance(result, dict)
        assert result.get("stat") != "OK" or "data" not in result

    def test_stat_not_ok_returns_error(self, monkeypatch):
        """TWSE 回傳 stat ≠ "OK" → 回傳錯誤訊息"""
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "twse")

        error_response = {
            "stat": "很抱歉，沒有符合條件的資料!",
            "total": 0,
        }

        def mock_get(*args, **kwargs):
            return FakeResponse(json_data=error_response)

        monkeypatch.setattr("data_fetcher.requests.get", mock_get)

        result = fetch_stock_data("9999")
        assert result["stat"] == "很抱歉，沒有符合條件的資料!"
        assert "data" not in result

    def test_first_month_fails_stops_immediately(self, monkeypatch):
        """第一個月就失敗 → 不繼續查後續月份，直接告知無法連線"""
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "twse")

        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.ConnectionError("Connection refused")

        monkeypatch.setattr("data_fetcher.requests.get", mock_get)

        result = fetch_stock_data("2330")

        # 第一次就失敗 → 只呼叫 1 次
        assert call_count == 1
        assert result.get("stat") != "OK"

    def test_second_month_fails_uses_partial_data(self, monkeypatch):
        """第二個月失敗 → 用第一個月的資料繼續"""
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "twse")
        # 跳過 time.sleep 加速測試
        monkeypatch.setattr("data_fetcher.time.sleep", lambda _: None)

        call_count = 0
        month_data = make_month_data(10)  # 第一個月 10 筆

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return FakeResponse(json_data=month_data)
            else:
                raise requests.exceptions.Timeout("Timeout")

        monkeypatch.setattr("data_fetcher.requests.get", mock_get)

        result = fetch_stock_data("2330")

        # 第一個月成功，第二個月失敗 → 用部分資料
        assert result["stat"] == "OK"
        assert len(result["data"]) == 10


# ============================================================
# B-5: 資料來源切換
# ============================================================


class TestSeedModeNoNetwork:
    """seed 模式不應發出任何外部網路請求。"""

    def test_seed_mode_no_network_call(self, monkeypatch):
        """seed 模式下，requests.get 不被呼叫"""
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "seed")

        def mock_get_should_not_be_called(*args, **kwargs):
            raise AssertionError("seed 模式不應呼叫 requests.get")

        monkeypatch.setattr("data_fetcher.requests.get", mock_get_should_not_be_called)

        # 不應 raise AssertionError
        result = fetch_stock_data("2330")
        assert result["stat"] == "OK"


class TestTwseModeCallsNetwork:
    """twse 模式確實透過網路取得資料。"""

    def test_twse_mode_calls_requests_get(self, monkeypatch):
        """twse 模式下，requests.get 至少被呼叫 1 次"""
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "twse")
        monkeypatch.setattr("data_fetcher.time.sleep", lambda _: None)

        call_count = 0
        month_data = make_month_data(15)

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return FakeResponse(json_data=month_data)

        monkeypatch.setattr("data_fetcher.requests.get", mock_get)

        fetch_stock_data("2330")
        assert call_count >= 1


class TestBothModesSameStructure:
    """兩種模式回傳的 JSON 結構一致。"""

    def test_seed_and_twse_have_same_keys(self, monkeypatch):
        """seed 與 twse 回傳的頂層 keys 相同"""
        # seed 模式
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "seed")
        seed_result = fetch_stock_data("2330")
        seed_keys = set(seed_result.keys())

        # twse 模式（mock）
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "twse")
        monkeypatch.setattr("data_fetcher.time.sleep", lambda _: None)

        month_data = make_month_data(15)

        def mock_get(*args, **kwargs):
            return FakeResponse(json_data=month_data)

        monkeypatch.setattr("data_fetcher.requests.get", mock_get)

        twse_result = fetch_stock_data("2330")
        twse_keys = set(twse_result.keys())

        assert seed_keys == twse_keys


class TestRequestInterval:
    """多次查詢間有適當延遲。"""

    def test_sleep_called_between_requests(self, monkeypatch):
        """查 3 個月時 time.sleep 至少被呼叫 1 次，秒數 >= 0.5"""
        monkeypatch.setattr("data_fetcher.DATA_SOURCE", "twse")

        sleep_calls = []

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr("data_fetcher.time.sleep", mock_sleep)

        # 每月只回傳 5 筆，迫使 fetcher 查完 3 個月
        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return FakeResponse(json_data=make_month_data(5, f"{5 - call_count:02d}"))

        monkeypatch.setattr("data_fetcher.requests.get", mock_get)

        fetch_stock_data("2330")

        # 至少有 1 次 sleep
        assert len(sleep_calls) >= 1
        # 每次延遲 >= 0.5 秒
        for s in sleep_calls:
            assert s >= 0.5, f"延遲僅 {s} 秒，不足 0.5 秒"
