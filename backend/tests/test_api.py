"""
API 回應契約與整合測試。

對應 test-plan.md：
  - B-4 API 回應契約
  - B-5 資料來源切換
"""

import re

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    """建立 FastAPI test client，強制使用 seed 模式。

    注意：data_fetcher 用 `from config import DATA_SOURCE` 取值，
    所以要 patch data_fetcher.DATA_SOURCE 而非 config.DATA_SOURCE。
    """
    monkeypatch.setattr("data_fetcher.DATA_SOURCE", "seed")
    from main import app

    return TestClient(app)


# ============================================================
# B-4.1: 成功回應結構
# ============================================================


class TestSuccessResponse:
    """成功回應的 JSON 結構驗證"""

    def test_has_stock_object(self, client):
        resp = client.get("/api/stock/2330")
        body = resp.json()
        assert "stock" in body
        assert isinstance(body["stock"]["code"], str)
        assert isinstance(body["stock"]["name"], str)
        assert body["stock"]["code"] != ""
        assert body["stock"]["name"] != ""

    def test_has_data_array(self, client):
        resp = client.get("/api/stock/2330")
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)
        assert len(body["data"]) > 0

    def test_data_row_fields(self, client):
        resp = client.get("/api/stock/2330")
        row = resp.json()["data"][0]
        required_fields = {"date", "open", "high", "low", "close", "volume", "ma5", "ma20"}
        assert required_fields.issubset(row.keys())

    def test_date_format_iso(self, client):
        resp = client.get("/api/stock/2330")
        for row in resp.json()["data"]:
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", row["date"]), (
                f'日期格式不符：{row["date"]}'
            )

    def test_close_is_number(self, client):
        resp = client.get("/api/stock/2330")
        for row in resp.json()["data"]:
            assert isinstance(row["close"], (int, float))

    def test_ma5_is_number_or_null(self, client):
        resp = client.get("/api/stock/2330")
        for row in resp.json()["data"]:
            assert row["ma5"] is None or isinstance(row["ma5"], (int, float))

    def test_ma20_is_number_or_null(self, client):
        resp = client.get("/api/stock/2330")
        for row in resp.json()["data"]:
            assert row["ma20"] is None or isinstance(row["ma20"], (int, float))

    def test_has_analysis(self, client):
        resp = client.get("/api/stock/2330")
        body = resp.json()
        assert "analysis" in body
        # 2330 有 36 筆 seed data，應能產生分析
        assert body["analysis"] is None or isinstance(body["analysis"], str)

    def test_has_warnings_array(self, client):
        resp = client.get("/api/stock/2330")
        body = resp.json()
        assert "warnings" in body
        assert isinstance(body["warnings"], list)

    def test_no_internal_fields_leaked(self, client):
        """回應不包含 _ 開頭的內部欄位"""
        resp = client.get("/api/stock/2330")
        for row in resp.json()["data"]:
            internal = [k for k in row.keys() if k.startswith("_")]
            assert internal == [], f"內部欄位外洩：{internal}"


# ============================================================
# B-4.2: 錯誤回應結構
# ============================================================


class TestErrorResponse:
    """錯誤回應的結構驗證"""

    def test_invalid_code_has_error_field(self, client):
        resp = client.get("/api/stock/invalid")
        body = resp.json()
        assert "error" in body
        assert isinstance(body["error"], str)
        assert len(body["error"]) > 0

    def test_error_message_is_user_readable(self, client):
        resp = client.get("/api/stock/invalid")
        error = resp.json()["error"]
        # 不應包含程式碼路徑或 stack trace
        assert "Traceback" not in error
        assert "\\" not in error  # Windows 路徑
        assert "/" not in error or "符合" in error  # 允許 TWSE 原始訊息


# ============================================================
# B-4.3: 一致性與完整性
# ============================================================


class TestConsistency:
    """回應的一致性驗證"""

    def test_idempotent(self, client):
        """同一代號連續查詢兩次，結果一致"""
        resp1 = client.get("/api/stock/2330").json()
        resp2 = client.get("/api/stock/2330").json()
        assert resp1 == resp2

    def test_dates_strictly_ascending(self, client):
        resp = client.get("/api/stock/2330")
        dates = [d["date"] for d in resp.json()["data"]]
        for i in range(1, len(dates)):
            assert dates[i] > dates[i - 1], f"日期未遞增：{dates[i-1]} → {dates[i]}"

    def test_data_length_matches_warnings(self, client):
        """data 不足 30 筆時 warnings 應提及"""
        resp = client.get("/api/stock/0050")
        body = resp.json()
        if len(body["data"]) < 30:
            assert any("不足 30" in w for w in body["warnings"])

    def test_dates_are_trading_days(self, client):
        """回傳的所有日期皆為交易日（不含週末）"""
        from datetime import datetime

        resp = client.get("/api/stock/2330")
        dates = [d["date"] for d in resp.json()["data"]]
        for date_str in dates:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            # weekday(): 0=Mon, 4=Fri, 5=Sat, 6=Sun
            assert dt.weekday() < 5, f"{date_str} 不是工作日（{dt.strftime('%A')}）"


# ============================================================
# B-4.4: 無效輸入
# ============================================================


class TestInvalidInput:
    """無效輸入的處理"""

    def test_nonexistent_code(self, client):
        resp = client.get("/api/stock/9999")
        body = resp.json()
        assert "error" in body or body["data"] == []

    def test_invalid_returns_empty_data(self, client):
        resp = client.get("/api/stock/invalid")
        body = resp.json()
        assert body["data"] == []

    def test_empty_string_code(self, client):
        """空字串 → 404 或回傳錯誤，不回傳正常資料"""
        # FastAPI 路徑參數空字串會匹配不到 → 預期 404
        # 用 /api/stock/ 與 /api/stock/%20 兩種情境
        resp1 = client.get("/api/stock/")
        # 應為 404 或 405（路由不匹配）
        assert resp1.status_code in (404, 405)

        # 用 URL-encoded 空白字元
        resp2 = client.get("/api/stock/%20")
        if resp2.status_code == 200:
            body = resp2.json()
            assert "error" in body or body["data"] == []

    def test_non_numeric_code(self, client):
        """非數字字串 → 回傳錯誤或空資料，不 crash"""
        resp = client.get("/api/stock/abcd")
        assert resp.status_code == 200  # API 不應 crash
        body = resp.json()
        assert "error" in body or body["data"] == []

    def test_special_characters_code(self, client):
        """特殊字元 → 不觸發非預期行為"""
        # 嘗試幾種可能引發 SQL injection / 路徑遍歷 的字串
        for code in ["23;30", "../etc", "<script>", "2330'"]:
            resp = client.get(f"/api/stock/{code}")
            # 不應 5xx，最多回傳 200 + error 或 404
            assert resp.status_code < 500, f"代號 {code} 觸發伺服器錯誤"
            if resp.status_code == 200:
                body = resp.json()
                # 不應回傳正常股票資料
                assert "error" in body or body["data"] == []


# ============================================================
# B-4.5: 資料來源異常（需 mock）— 僅驗 seed 模式行為
# ============================================================


class TestDataSourceSeed:
    """seed 模式的行為驗證"""

    def test_seed_mode_returns_data(self, client):
        resp = client.get("/api/stock/2330")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) > 0

    def test_seed_few_has_warnings(self, client):
        """few seed 資料不足 → 有警告"""
        resp = client.get("/api/stock/few")
        body = resp.json()
        assert any("不足" in w for w in body["warnings"])


# ============================================================
# B-4.6: 資料可信度 (warnings 透過 API 回傳)
# ============================================================


class TestWarningsThroughAPI:
    """透過 API 驗證 warnings"""

    def test_insufficient_data_warning(self, client):
        resp = client.get("/api/stock/0050")
        body = resp.json()
        if len(body["data"]) < 30:
            assert len(body["warnings"]) > 0

    def test_no_warnings_clean_data(self, client):
        """2330 有 36 筆完整 seed → 截取 30 筆後不應有不足警告"""
        resp = client.get("/api/stock/2330")
        body = resp.json()
        assert not any("不足" in w for w in body["warnings"])
