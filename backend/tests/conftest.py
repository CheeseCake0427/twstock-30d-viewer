import json
import pathlib
import sys

import pytest

# 讓 tests/ 能 import backend 的模組
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    """載入 fixtures 目錄下的 JSON 檔案。

    用法：
        def test_something(load_fixture):
            data = load_fixture("normal_30.json")
    """

    def _load(filename: str) -> dict:
        filepath = FIXTURES_DIR / filename
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)

    return _load
