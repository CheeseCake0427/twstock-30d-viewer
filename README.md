# twstock-30d-viewer

台股代號查詢工具：輸入股票代號，查看最近 30 個交易日的 OHLC 走勢、MA5/MA20 均線，以及基於實際數據的繁體中文分析。

## 功能

- 查詢最近 30 個交易日的 OHLC（開高低收）與成交量
- 計算 MA5（5 日均線）與 MA20（20 日均線）
- 走勢圖 + 均線視覺化（Recharts）
- 三套前端主題：**入門版** / **專業版** / **樂齡版**
- 可信的繁中資料描述（非投資建議）
  - 事實提取層：價格變化、MA 關係、MA 交叉、近 5 日趨勢、期間高低點
  - 文字生成層：預設走固定模板；若設定 `AI_API_KEY`，改由 LLM 改寫並經「數字比對 + 禁用詞」驗證，失敗自動降級回模板

## 可信度保護

系統遵循「**寧可少顯示，不可誤顯示**」原則，以下條件會觸發明確的警告或拒絕輸出：

| 情境 | 觸發條件 | 系統行為 |
|---|---|---|
| 連線失敗（第一個月） | TWSE API 無回應 | 回傳 `error` 欄位，不輸出圖表 |
| 資料筆數不足 30 | `total < 30` | 有多少算多少，加 warning |
| 無法計算 MA5 | `total < 5` | MA5 欄位填 `null`，加 warning |
| 無法計算 MA20 | `total < 20` | MA20 欄位填 `null`，加 warning |
| 日期順序錯亂 | 非嚴格遞增 | 自動重新排序，加 warning |
| 收盤價為空 / 0 / 負數 | 核心欄位異常 | 整筆略過不納入 MA 計算，加 warning |
| 其他 OHL 欄位為空 | 輔助欄位異常 | 保留該筆但加 warning，提示圖表可能異常 |
| 單日漲跌幅 > 50% | 可能為解析錯誤 | 保留該筆但加 warning |
| AI 分析資料天數不足 | `total < 10` | 回傳「依據不足，無法產生分析」 |
| AI 分析略過比例過高 | 被略過筆數 > 30% | 回傳「依據不足，無法產生分析」 |
| AI 分析事實不足 | 事實提取 < 2 項 | 回傳「依據不足，無法產生分析」 |
| LLM 改寫輸出驗證失敗 | 出現原始事實外的數字，或命中禁用詞 | 降級回模板模式 |

## 技術棧

- **Backend**：Python 3.13 + FastAPI + uvicorn，資料來源為 TWSE 傳統 API（`STOCK_DAY`）
- **Frontend**：React 19 + Vite 8 + TypeScript + Recharts
- **Testing**：pytest（backend）、Vitest + Testing Library（frontend unit）、Playwright（E2E）

## 專案結構

```
twstock-30d-viewer/
├── backend/
│   ├── main.py                  # FastAPI 入口，GET /api/stock/{code}
│   ├── config.py                # DATA_SOURCE / AI_API_KEY / IDLE_SHUTDOWN_MINUTES
│   ├── data_fetcher.py          # TWSE 呼叫 + seed 檔讀取
│   ├── data_processor.py        # 民國曆轉換、清洗、MA 計算、異常偵測
│   ├── ai_analyzer.py           # 事實提取 + AI 改寫 + 數字驗證
│   ├── analysis_templates.py    # 文字模板與禁用詞
│   └── tests/                   # pytest 單元測試與 fixtures
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # 三主題 Tab + 共用搜尋列
│   │   ├── api.ts               # fetch 封裝（VITE_API_BASE_URL 可覆寫）
│   │   ├── components/          # SearchBar / StockChart / AnalysisPanel / Warnings
│   │   └── themes/              # Beginner / Pro / Elderly 三套
│   ├── vite.config.ts           # /api proxy 到 backend
│   └── tests/                   # Vitest 單元測試
├── tests/                       # Playwright E2E
├── seed/                        # TWSE 原始 JSON（離線開發與測試）
└── docs/                        # 設計文件：roadmap / risk / test-plan ...
```

## 快速開始

### 1. Backend

```bash
# 建立 venv 並安裝套件
python -m venv .venv
.venv/Scripts/activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r backend/requirements.txt

# 啟動（預設 port 8082，對應 frontend 的 proxy target）
cd backend
uvicorn main:app --host 127.0.0.1 --port 8082 --reload
```

- Swagger UI：<http://127.0.0.1:8082/docs>
- 健康測試：`curl http://127.0.0.1:8082/api/stock/2330`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                       # http://127.0.0.1:5173
```

Vite dev server 會自動將 `/api/*` 代理到 backend，無須設 CORS 或硬編碼 URL。打開 <http://127.0.0.1:5173>，輸入股票代號（如 `2330`、`2454`、`0050`）即可查詢。

## 環境變數

所有變數皆為選填，未設定時使用合理預設值。

### Backend

| 變數 | 預設 | 設定位置 | 說明 |
|---|---|---|---|
| `AI_API_KEY` | `""` | env | 有值則啟用 AI 改寫；為空則使用模板模式 |
| `IDLE_SHUTDOWN_MINUTES` | `0` | env | `> 0` 時啟用閒置自動關閉（分鐘），避免本地服務長期佔 port |
| `DATA_SOURCE` | `"twse"` | `backend/config.py` | `twse`：呼叫 TWSE API；`seed`：改讀 `seed/` 目錄的 JSON（離線開發用）。目前為檔案常數，需改檔 |

### Frontend（`frontend/.env`，可參考 `.env.example`）

| 變數 | 預設 | 說明 |
|---|---|---|
| `VITE_API_PROXY_TARGET` | `http://127.0.0.1:8082` | dev / preview server 將 `/api` proxy 的目標 URL |
| `VITE_API_BASE_URL` | `""`（同 origin） | 前後端分開部署時直接作為 fetch 的 base URL |

## API

### `GET /api/stock/{code}`

**正常回應**

```json
{
  "stock": { "code": "2330", "name": "台積電" },
  "data": [
    {
      "date": "2026-04-10",
      "open": 1900.0,
      "high": 1920.0,
      "low": 1895.0,
      "close": 1910.0,
      "volume": 54321000,
      "ma5": 1902.5,
      "ma20": null
    }
  ],
  "analysis": "近 30 個交易日中...",
  "warnings": ["資料僅 22 個交易日，不足 30 日"],
  "extra": null
}
```

**查無資料 / 無效代號**

```json
{
  "stock": { "code": "XYZ", "name": "" },
  "data": [],
  "analysis": null,
  "warnings": [],
  "extra": null,
  "error": "很抱歉，沒有符合條件的資料!"
}
```

## 測試

```bash
# Backend 單元測試
.venv/Scripts/activate
cd backend && pytest

# Frontend 單元測試
cd frontend && npm test

# E2E（需先啟動 backend + frontend）
cd tests && npm install && npx playwright test
```

## 決策備忘與範圍取捨

本專案為 3 小時限時的 full-stack 測驗。以下是關鍵的取捨與理由：

### 刻意納入範圍

- **Seed / TWSE 雙資料來源切換**：離線開發不被網路狀況卡住，並保留 `seed/` 作為可重現的測試 fixture
- **兩層 AI 分析架構**：事實提取層用純 Python、文字生成層預設走模板，`AI_API_KEY` 有設才呼叫 LLM。即使 AI 服務掛掉，系統仍能產出可信文字
- **LLM 輸出後處理驗證**：數字比對 + 禁用詞表，驗證失敗自動降級。prompt 約束不等於行為保證，需要程式層面的防線
- **三套前端主題**：相同 API 資料、不同呈現風格（入門 / 專業 / 樂齡），展示關注點分離
- **單一資料來源原則**：歷史股價計算全程使用同一來源，從架構層面消除跨來源數值不一致的風險

### 刻意捨棄或延後

- **`extra` 欄位（本益比、殖利率等 TWSE OpenAPI 資料）**：API 回應保留了 `extra` 位置但目前永遠為 `null`。實作需處理 TWSE OpenAPI（`1150402`）與 TWSE 傳統 API（`115/04/02`）的日期格式差異，已在 `_roc_to_ad()` 預先支援，但完整串接留待後續
- **響應式 / mobile 版面**：桌面優先，手機斷點未調校
- **`pandas` / `numpy`**：核心計算只有滑動平均與陣列操作，純 Python 足夠，不引入重型依賴
- **HTTP 客戶端套件**：前端用原生 `fetch`、後端用 `requests`，不引入 axios / httpx（除了 AI 改寫用到 `httpx` 因為要 timeout 控制）
- **資料持久化**：沒有資料庫、沒有快取層。每次請求即時打 TWSE，用 `0.5s` 間隔避免被擋

### 已知限制

- **TWSE SSL 憑證**：部分環境會失敗，目前以 `verify=False` 處理並壓 urllib3 warning
- **TWSE 速率**：同股票短時間重複查詢可能被擋，沒有做指數退避

更完整的風險處理與 P0/P1/P2 分級實作紀錄見 `docs/risk-handling.md`。

## 設計備忘

更多設計細節見 `docs/`：

- `roadmap.md` — 開發階段規劃與技術選型理由
- `risk-handling.md` — 資料可信度與異常處理策略
- `test-plan.md` — 測試策略與涵蓋範圍
- `module-design.md` — 各模組職責與邊界
- `origin-spec.md` — 原始需求
- `environment.md` — 環境設定備忘

## License

MIT（見 `LICENSE`）
