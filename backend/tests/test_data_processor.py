"""
資料清洗與技術指標計算測試。

對應 test-plan.md：
  - B-1 資料清洗與轉換
  - B-2 技術指標計算
"""

from data_processor import process_stock_data, _roc_to_ad, _to_float


# ============================================================
# B-1: 資料清洗與轉換
# ============================================================


class TestRocToAd:
    """B-1.1 民國曆轉換"""

    def test_normal(self):
        assert _roc_to_ad("115/04/01") == "2026-04-01"

    def test_cross_year(self):
        assert _roc_to_ad("115/01/02") == "2026-01-02"

    def test_previous_year(self):
        assert _roc_to_ad("114/12/31") == "2025-12-31"

    def test_roc_100(self):
        assert _roc_to_ad("100/01/01") == "2011-01-01"

    def test_invalid_format(self):
        assert _roc_to_ad("abc/de/fg") is None

    def test_missing_parts(self):
        assert _roc_to_ad("115-04-01") is None


class TestToFloat:
    """B-1.2 數值格式清洗"""

    def test_comma_removal(self):
        assert _to_float("1,870.00") == 1870.0

    def test_positive_sign(self):
        assert _to_float("+15.00") == 15.0

    def test_negative_sign(self):
        assert _to_float("-15.00") == -15.0

    def test_large_number(self):
        assert _to_float("47,389,975") == 47389975.0

    def test_empty_string(self):
        assert _to_float("") == 0.0

    def test_dash(self):
        assert _to_float("--") == 0.0


class TestRowCleaning:
    """B-1.3 整筆異常處理"""

    def test_insufficient_fields_skipped(self, load_fixture):
        raw = load_fixture("empty_fields.json")
        result = process_stock_data(raw)
        # row 3 只有 5 個欄位，應被略過
        dates = [d["date"] for d in result["data"]]
        assert "2026-03-04" not in dates
        assert any("略過" in w for w in result["warnings"])

    def test_empty_close_skipped(self, load_fixture):
        raw = load_fixture("empty_fields.json")
        result = process_stock_data(raw)
        # row 2 收盤價空字串，應被略過
        dates = [d["date"] for d in result["data"]]
        assert "2026-03-03" not in dates
        assert any("收盤價" in w and "空" in w for w in result["warnings"])

    def test_invalid_date_skipped(self, load_fixture):
        raw = load_fixture("empty_fields.json")
        result = process_stock_data(raw)
        # row 5 日期 abc/de/fg，應被略過
        assert any("略過" in w for w in result["warnings"])

    def test_zero_close_skipped(self, load_fixture):
        raw = load_fixture("zero_close.json")
        result = process_stock_data(raw)
        # 115/03/04 收盤價 0.00，應被略過
        dates = [d["date"] for d in result["data"]]
        assert "2026-03-04" not in dates
        assert any("異常為 0" in w for w in result["warnings"])

    def test_disordered_auto_sort(self, load_fixture):
        raw = load_fixture("disordered.json")
        result = process_stock_data(raw)
        dates = [d["date"] for d in result["data"]]
        # 排序後日期應嚴格遞增
        assert dates == sorted(dates)
        assert any("重新排序" in w for w in result["warnings"])


# ============================================================
# B-2: 技術指標計算
# ============================================================


class TestMA5:
    """B-2.1 MA5 正確性"""

    def test_ma5_matches_hand_calculation(self, load_fixture):
        fixture = load_fixture("with_ma_answers.json")
        result = process_stock_data(fixture["input"])
        expected = fixture["expected"]

        for row in result["data"]:
            exp = expected[row["date"]]
            assert row["ma5"] == exp["ma5"], (
                f'{row["date"]}: ma5={row["ma5"]}, expected={exp["ma5"]}'
            )

    def test_first_4_rows_ma5_null(self, load_fixture):
        fixture = load_fixture("with_ma_answers.json")
        result = process_stock_data(fixture["input"])
        for row in result["data"][:4]:
            assert row["ma5"] is None

    def test_5th_row_onward_ma5_has_value(self, load_fixture):
        fixture = load_fixture("with_ma_answers.json")
        result = process_stock_data(fixture["input"])
        for row in result["data"][4:]:
            assert row["ma5"] is not None

    def test_ma5_uses_only_close(self, load_fixture):
        """MA5 不受開盤價、最高價、最低價影響"""
        raw = load_fixture("normal_30.json")
        result1 = process_stock_data(raw)

        # 修改 open/high/low 但不改 close
        import copy

        raw2 = copy.deepcopy(raw)
        for row in raw2["data"]:
            row[3] = "999.00"  # open
            row[4] = "999.00"  # high
            row[5] = "1.00"  # low
        result2 = process_stock_data(raw2)

        for r1, r2 in zip(result1["data"], result2["data"]):
            assert r1["ma5"] == r2["ma5"]


class TestMA20:
    """B-2.2 MA20 正確性"""

    def test_ma20_matches_hand_calculation(self, load_fixture):
        fixture = load_fixture("with_ma_answers.json")
        result = process_stock_data(fixture["input"])
        expected = fixture["expected"]

        for row in result["data"]:
            exp = expected[row["date"]]
            assert row["ma20"] == exp["ma20"], (
                f'{row["date"]}: ma20={row["ma20"]}, expected={exp["ma20"]}'
            )

    def test_first_19_rows_ma20_null(self, load_fixture):
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        for row in result["data"][:19]:
            assert row["ma20"] is None

    def test_20th_row_onward_ma20_has_value(self, load_fixture):
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        for row in result["data"][19:]:
            assert row["ma20"] is not None


class TestMABoundary:
    """B-2.3 邊界情境"""

    def test_exactly_5_rows(self, load_fixture):
        raw = load_fixture("insufficient_5.json")
        result = process_stock_data(raw)
        ma5_values = [d["ma5"] for d in result["data"]]
        # 前 4 筆 null，第 5 筆有值
        assert ma5_values[:4] == [None, None, None, None]
        assert ma5_values[4] is not None
        # MA20 全 null
        assert all(d["ma20"] is None for d in result["data"])

    def test_exactly_20_rows(self, load_fixture):
        """恰好 20 筆 → MA20 僅最後 1 筆有值"""
        import copy

        raw = copy.deepcopy(load_fixture("insufficient_22.json"))
        # 截取前 20 筆
        raw["data"] = raw["data"][:20]
        raw["total"] = 20

        result = process_stock_data(raw)
        assert len(result["data"]) == 20
        # MA20：前 19 筆 null，第 20 筆有值
        ma20_values = [d["ma20"] for d in result["data"]]
        assert all(v is None for v in ma20_values[:19])
        assert ma20_values[19] is not None
        # 恰好 1 筆有值
        assert sum(1 for v in ma20_values if v is not None) == 1

    def test_exactly_30_rows(self, load_fixture):
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        ma5_count = sum(1 for d in result["data"] if d["ma5"] is not None)
        ma20_count = sum(1 for d in result["data"] if d["ma20"] is not None)
        assert ma5_count == 26  # 30 - 4
        assert ma20_count == 11  # 30 - 19

    def test_zero_rows(self):
        raw = {"stat": "OK", "title": "", "data": [], "total": 0}
        result = process_stock_data(raw)
        assert result["data"] == []
        assert any("無有效" in w for w in result["warnings"])

    def test_one_row(self):
        raw = {
            "stat": "OK",
            "title": "115年04月 9999 測試各日成交資訊",
            "data": [
                ["115/04/01", "100", "10000", "10.00", "11.00", "9.00", "10.00", "+1.00", "10"],
            ],
            "total": 1,
        }
        result = process_stock_data(raw)
        assert len(result["data"]) == 1
        assert result["data"][0]["ma5"] is None
        assert result["data"][0]["ma20"] is None

    def test_skipped_rows_still_compute_ma(self, load_fixture):
        """連續多筆異常 → 跳過後剩餘資料仍正確計算 MA"""
        raw = load_fixture("zero_close.json")
        result = process_stock_data(raw)
        # 7 筆中 1 筆被跳過 → 剩 6 筆
        assert len(result["data"]) == 6
        # 第 5 筆開始有 MA5
        ma5_values = [d["ma5"] for d in result["data"]]
        assert ma5_values[4] is not None


# ============================================================
# 資料完整性 warnings
# ============================================================


class TestWarnings:
    """B-4.6 (部分): 資料可信度 warnings"""

    def test_insufficient_30_warning(self, load_fixture):
        raw = load_fixture("insufficient_22.json")
        result = process_stock_data(raw)
        assert any("不足 30 日" in w for w in result["warnings"])

    def test_insufficient_5_warning(self, load_fixture):
        """不足 5 筆 → 有 MA5 警告"""
        raw = {
            "stat": "OK",
            "title": "115年04月 9999 測試各日成交資訊",
            "data": [
                ["115/04/01", "100", "10000", "10.00", "11.00", "9.00", "10.00", "+1.00", "10"],
                ["115/04/02", "100", "10000", "10.00", "11.00", "9.00", "11.00", "+1.00", "10"],
                ["115/04/03", "100", "10000", "10.00", "11.00", "9.00", "12.00", "+1.00", "10"],
            ],
            "total": 3,
        }
        result = process_stock_data(raw)
        assert any("MA5" in w for w in result["warnings"])

    def test_insufficient_20_warning(self, load_fixture):
        raw = load_fixture("insufficient_5.json")
        result = process_stock_data(raw)
        assert any("MA20" in w for w in result["warnings"])

    def test_no_warnings_for_complete_data(self, load_fixture):
        raw = load_fixture("normal_30.json")
        result = process_stock_data(raw)
        # 30 筆完整資料 → 不應有筆數不足或 MA 不足的警告
        assert not any("不足" in w for w in result["warnings"])

    def test_invalid_response_returns_error(self, load_fixture):
        raw = load_fixture("invalid_response.json")
        result = process_stock_data(raw)
        assert "error" in result
