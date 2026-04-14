# 環境說明

## 一、開發所使用的環境

### 作業系統

| 項目 | 版本 |
|---|---|
| OS | Windows 10 Pro 10.0.19045 |

### 執行環境

| 項目 | 版本 |
|---|---|
| Python | 3.13.12 |
| Node.js | 20.19.4 |
| npm | 10.8.2 |

### 後端依賴（Python）

| 套件 | 版本 | 用途 |
|---|---|---|
| fastapi | 0.115.12 | Web 框架 |
| uvicorn | 0.34.2 | ASGI 伺服器 |
| requests | 2.33.1 | TWSE API 呼叫 |

### 前端依賴（Node.js）

| 套件 | 版本 | 用途 |
|---|---|---|
| react | 19.2.4 | UI 框架 |
| react-dom | 19.2.4 | React DOM 渲染 |
| recharts | 3.8.1 | 圖表元件 |
| typescript | 6.0.2 | 型別檢查 |
| vite | 8.0.4 | 建置工具 / dev server |

---

## 二、可運行本專案的所需環境

### 最低需求

| 項目 | 最低版本 | 說明 |
|---|---|---|
| Python | 3.11+ | 使用了 `type A \| B` 語法及 `dict` 泛型標註 |
| Node.js | 18+ | Vite 8 要求 Node 18 以上 |
| npm | 8+ | 隨 Node 18 附帶 |
| 作業系統 | Windows / macOS / Linux 皆可 | 無平台特定依賴 |
| 網路 | 需要連外網（TWSE 模式） | seed 模式不需要網路 |

### 安裝與啟動

```bash
# 1. 後端
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8001

# 2. 前端（另一個終端）
cd frontend
npm install
npm run dev
```

啟動後打開 `http://localhost:5173` 即可使用。

### 設定檔說明

所有設定集中在 `backend/config.py`：

```python
DATA_SOURCE = "twse"  # "seed"：使用本地測試資料 / "twse"：使用 TWSE 即時 API
SEED_DIR = "../seed"
AI_API_KEY = ""       # 空字串：使用模板分析 / 填入 OpenAI API Key：啟用 AI 改寫
```

| 設定 | 值 | 說明 |
|---|---|---|
| `DATA_SOURCE` | `"seed"` | 使用 `seed/` 目錄下的本地 JSON，不需網路，適合開發與測試 |
| | `"twse"` | 即時呼叫 TWSE 傳統網站 API，需要網路連線 |
| `AI_API_KEY` | `""` (空) | AI 分析使用規則引擎模板生成，不依賴外部服務 |
| | `"sk-..."` | AI 分析改由 OpenAI API 改寫為更流暢的文字，失敗時自動降級為模板 |

`AI_API_KEY` 也可透過環境變數設定，不需修改程式碼：

```bash
# Linux / macOS
AI_API_KEY=sk-your-key python -m uvicorn main:app --port 8001

# Windows PowerShell
$env:AI_API_KEY="sk-your-key"; python -m uvicorn main:app --port 8001

# Windows CMD
set AI_API_KEY=sk-your-key && python -m uvicorn main:app --port 8001
```

---

## 三、專案目錄結構

```
twstock-30d-viewer/
├── backend\
│   ├── main.py                ← FastAPI 入口
│   ├── config.py              ← 集中設定（資料來源、AI Key）
│   ├── data_fetcher.py        ← L1 資料取得層（seed / TWSE 可切換）
│   ├── data_processor.py      ← L2 資料處理層（清洗、MA 計算、warnings）
│   ├── ai_analyzer.py         ← L3 AI 分析層（事實提取 + 文字生成）
│   ├── analysis_templates.py  ← 分析文字模板（獨立維護）
│   └── requirements.txt       ← Python 依賴清單
├── frontend\
│   ├── src\
│   │   ├── App.tsx            ← 主頁面（Tab 切換 + 共用搜尋列）
│   │   ├── App.css            ← 共用樣式（Tab、搜尋列）
│   │   ├── api.ts             ← 後端 API 呼叫封裝
│   │   ├── types.ts           ← TypeScript 型別定義
│   │   ├── themes\
│   │   │   ├── types.ts           ← 主題共用介面
│   │   │   ├── BeginnerTheme.tsx  ← 入門版主題
│   │   │   ├── BeginnerTheme.css
│   │   │   ├── ProTraderTheme.tsx ← 專業版主題
│   │   │   ├── ProTraderTheme.css
│   │   │   ├── ElderlyTheme.tsx   ← 樂齡版主題
│   │   │   └── ElderlyTheme.css
│   │   └── components\
│   │       ├── SearchBar.tsx      ← （已移至 App 層級）
│   │       ├── StockChart.tsx     ← （已整合至各主題）
│   │       ├── Warnings.tsx       ← （已整合至各主題）
│   │       └── AnalysisPanel.tsx  ← （已整合至各主題）
│   ├── package.json
│   └── vite.config.ts
├── seed\
│   ├── stock_2330.json        ← 台積電 36 筆真實資料
│   ├── stock_0050.json        ← 元大台灣50 22 筆真實資料
│   ├── stock_few.json         ← 異常測試（5 筆，含空值）
│   └── stock_invalid.json     ← 異常測試（代號不存在）
├── origin-spec.md             ← 需求規格書
├── module-design.md           ← 模組設計書
├── roadmap.md                 ← 開發 Roadmap
└── environment.md             ← 本文件
```
