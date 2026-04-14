# 開發 Roadmap

## 技術選型

### 前端

| 項目 | 選擇 | 理由 |
|---|---|---|
| 框架 | React + TypeScript | 元件化開發，型別安全，生態成熟 |
| 建置工具 | Vite | 啟動快、HMR 即時、設定簡潔 |
| 圖表 | Recharts | 基於 React 的宣告式圖表庫，折線圖 + tooltip 支援好 |
| HTTP | fetch (原生) | 需求簡單，單一端點，不需額外套件 |
| 樣式 | CSS Modules 或 Tailwind CSS | 依偏好選擇，避免樣式衝突即可 |

### 後端

| 項目 | 選擇 | 理由 |
|---|---|---|
| 框架 | FastAPI (Python) | 非同步、自帶 OpenAPI 文件、型別提示、輕量 |
| 資料處理 | 純 Python（不引入 pandas） | 需求僅為陣列操作 + 移動平均，不需重型套件 |
| AI 呼叫 | OpenAI / Anthropic SDK（依可用 API Key 決定） | 後端呼叫，不暴露 key 給前端 |
| CORS | fastapi.middleware.cors | 允許前端 dev server 跨域請求 |

### 前後端溝通

```
Frontend (Vite dev :5173)  ──  GET /api/stock/{code}  ──▶  Backend (FastAPI :8000)
```

---

## 開發階段

### Phase 0：專案骨架搭建

**目標**：前後端能各自啟動、互相通訊

| 步驟 | 工作內容 | 產出 |
|---|---|---|
| 0-1 | 建立專案目錄結構 | 見下方目錄結構 |
| 0-2 | 後端：初始化 FastAPI，建立 `GET /api/stock/{code}` 回傳假資料 | 能啟動、能回 JSON |
| 0-3 | 前端：初始化 Vite + React + TypeScript | 能啟動、能顯示頁面 |
| 0-4 | 前端呼叫後端 API 確認通訊正常 | 跨域無誤、JSON 能解析 |

**目錄結構**：

```
twstock-30d-viewer/
  ├── backend\
  │     ├── main.py              ← FastAPI 入口
  │     ├── config.py            ← DATA_SOURCE 等設定
  │     ├── data_fetcher.py      ← L1 資料取得層
  │     ├── data_processor.py    ← L2 資料處理層
  │     ├── ai_analyzer.py       ← L3 AI 分析層
  │     └── requirements.txt     ← Python 依賴
  ├── frontend\
  │     ├── src\
  │     │     ├── App.tsx         ← 主頁面
  │     │     ├── components\
  │     │     │     ├── SearchBar.tsx     ← 股票代號輸入
  │     │     │     ├── StockChart.tsx    ← 走勢圖 + MA 曲線
  │     │     │     ├── AnalysisPanel.tsx ← AI 分析區塊
  │     │     │     └── Warnings.tsx      ← 資料可信度警告
  │     │     ├── types.ts        ← API 回應型別定義
  │     │     └── api.ts          ← 呼叫後端 API
  │     ├── package.json
  │     └── vite.config.ts
  ├── seed\
  │     ├── stock_2330.json
  │     ├── stock_0050.json
  │     └── stock_invalid.json
  ├── origin-spec.md
  ├── module-design.md
  └── roadmap.md
```

---

### Phase 1：Seed Data + 資料處理（後端核心）

**目標**：用 seed data 跑通「查詢 → 清洗 → 計算 MA → 回傳」的完整後端流程

| 步驟 | 工作內容 | 對應模組 |
|---|---|---|
| 1-1 | 產生 seed data（從 TWSE API 抓一次真實資料存成 JSON） | L1 / Seed Data 策略 |
| 1-2 | 實作 `data_fetcher.py`：seed 模式讀取本地 JSON | L1 Data Fetcher |
| 1-3 | 實作 `data_processor.py`：民國曆轉換、去逗號、字串轉數字 | L2（清洗） |
| 1-4 | 實作 `data_processor.py`：截取最近 30 筆、計算 MA5/MA20 | L2（計算）/ F2 |
| 1-5 | 實作 `data_processor.py`：資料完整性檢查，產生 warnings | L2（檢查）/ F5 |
| 1-6 | 串接 `main.py`：`GET /api/stock/{code}` 回傳完整 JSON 結構 | L4 Backend API |

**Phase 1 驗收標準**：
- `GET /api/stock/2330` 回傳 30 筆含 MA5/MA20 的結構化資料
- `GET /api/stock/invalid` 回傳錯誤訊息
- warnings 能正確反映資料不足、欄位缺漏等情況

---

### Phase 2：前端顯示（圖表 + 輸入 + 警告）

**目標**：使用者能在畫面上輸入代號、看到走勢圖與警告

| 步驟 | 工作內容 | 對應模組 |
|---|---|---|
| 2-1 | 定義 `types.ts`：前後端 API 回應的 TypeScript 型別 | L5 |
| 2-2 | 實作 `api.ts`：封裝 `GET /api/stock/{code}` | L5 |
| 2-3 | 實作 `SearchBar.tsx`：輸入框 + 查詢按鈕 + loading 狀態 | L5 / F1（前端部分） |
| 2-4 | 實作 `StockChart.tsx`：Recharts 折線圖（收盤價 + MA5 + MA20） | L5 / F3 |
| 2-5 | 實作 `Warnings.tsx`：醒目顯示 warnings 列表 | L5 / F5（前端部分） |
| 2-6 | 實作 `App.tsx`：組合以上元件，串接資料流 | L5 |
| 2-7 | 處理錯誤狀態：代號無效、API 失敗的 UI 顯示 | L5 |

**Phase 2 驗收標準**：
- 輸入 `2330` → 顯示走勢圖，三條線（收盤價、MA5、MA20）顏色區分
- 滑鼠懸停 tooltip 顯示當日數值
- 輸入無效代號 → 顯示錯誤提示
- 資料不足時 → 顯示黃色警告區塊

---

### Phase 3：AI 分析

**目標**：後端產生繁中分析文字，前端顯示

| 步驟 | 工作內容 | 對應模組 |
|---|---|---|
| 3-1 | 設計 prompt 模板：注入數據事實 + 約束條件 | L3 / F4 |
| 3-2 | 實作 `ai_analyzer.py`：組裝 prompt、呼叫 AI API、解析回應 | L3 |
| 3-3 | 加入依據不足判斷：資料 < 20 筆或 warnings 過多時拒絕產生分析 | L3 / F5 |
| 3-4 | 串接 `main.py`：將 analysis 欄位加入 API 回應 | L4 |
| 3-5 | 實作 `AnalysisPanel.tsx`：顯示分析文字 + 「AI 生成內容」標註 | L5 / F4 |
| 3-6 | 處理 AI API 失敗：前端顯示「分析功能暫時無法使用」 | L5 |

**Phase 3 驗收標準**：
- 分析文字為繁體中文，引用 ≥ 2 項具體數據
- 不包含投資建議或預測用語
- 資料不足時顯示「依據不足，無法產生分析」
- AI API 掛掉時不影響圖表顯示

---

### Phase 4：接入 TWSE 真實 API

**目標**：從 seed data 切換為 TWSE 即時資料

| 步驟 | 工作內容 | 對應模組 |
|---|---|---|
| 4-1 | 實作 `data_fetcher.py`：TWSE 模式（多月查詢 + 合併 + 0.5s 間隔） | L1 |
| 4-2 | `config.py` 切換 `DATA_SOURCE = "twse"` | L1 |
| 4-3 | 端對端驗證：多支股票（大型股、ETF、冷門股） | 全模組 |
| 4-4 | 處理 TWSE 特殊回應：被擋、無資料、格式異常 | L1 / F5 |

**Phase 4 驗收標準**：
- `2330`（台積電）、`0050`（元大台灣50）、`2317`（鴻海）查詢正常
- 冷門股資料不足時 warnings 正確顯示
- 無效代號正確提示

---

### Phase 5：收尾打磨

**目標**：補強邊界情境、UI 細節

| 步驟 | 工作內容 |
|---|---|
| 5-1 | 前端 loading 體驗：查詢中顯示 spinner（TWSE 需 2~3 次請求，約 2 秒） |
| 5-2 | 補充 TWSE OpenAPI / 本地 JSON 的 extra 資訊（本益比、殖利率）顯示在前端 |
| 5-3 | 響應式佈局：手機 / 桌面皆可正常瀏覽 |
| 5-4 | 最終端對端測試，確認所有 warnings 與錯誤路徑正常 |

---

## 各 Phase 對應功能模組覆蓋

| Phase | F1 查詢 | F2 指標 | F3 圖表 | F4 AI | F5 可信度 |
|---|---|---|---|---|---|
| Phase 0 | 骨架 | - | - | - | - |
| Phase 1 | **完成** | **完成** | - | - | **完成**（後端） |
| Phase 2 | 前端串接 | 前端顯示 | **完成** | - | **完成**（前端） |
| Phase 3 | - | - | - | **完成** | 補強判斷 |
| Phase 4 | 切換真實 API | 驗證 | 驗證 | 驗證 | 驗證 |
| Phase 5 | - | - | 打磨 | - | 打磨 |

---

## 開發順序原則

1. **後端先行**：先確保 API 回傳正確的結構化資料，前端才有東西接
2. **Seed Data 優先**：用靜態資料開發所有邏輯，最後才接真實 API，避免被網路問題卡住
3. **核心功能先做，AI 後加**：圖表 + 指標是主幹，AI 分析是加值，即使 AI 掛了系統仍可用
4. **每個 Phase 可獨立驗收**：不會出現「全部做完才能看到東西」的情況
