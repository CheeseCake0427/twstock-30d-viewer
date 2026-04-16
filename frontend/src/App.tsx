import { lazy, Suspense, useState } from "react";
import { fetchStock } from "./api";
import type { StockResponse } from "./types";
import "./App.css";

const ElderlyTheme = lazy(() => import("./themes/ElderlyTheme"));
const ProTraderTheme = lazy(() => import("./themes/ProTraderTheme"));
const BeginnerTheme = lazy(() => import("./themes/BeginnerTheme"));

type ThemeKey = "beginner" | "pro" | "elderly";

const THEMES: { key: ThemeKey; label: string; desc: string }[] = [
  { key: "beginner", label: "入門版", desc: "股票新手適用" },
  { key: "pro", label: "專業版", desc: "資深操作師" },
  { key: "elderly", label: "樂齡版", desc: "大字體友善介面" },
];

function App() {
  const [theme, setTheme] = useState<ThemeKey>("beginner");
  const [code, setCode] = useState("");
  const [result, setResult] = useState<StockResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    const trimmed = code.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await fetchStock(trimmed);
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "未知錯誤");
    } finally {
      setLoading(false);
    }
  };

  const themeProps = { result, error, loading };

  return (
    <div className="app-shell" data-theme={theme}>
      {/* Tab 切換列 */}
      <nav className="theme-tabs">
        {THEMES.map((t) => (
          <button
            key={t.key}
            className={`theme-tab ${theme === t.key ? "active" : ""}`}
            onClick={() => setTheme(t.key)}
          >
            <span className="tab-label">{t.label}</span>
            <span className="tab-desc">{t.desc}</span>
          </button>
        ))}
      </nav>

      {/* 共用搜尋列 */}
      <div className="global-search">
        <div className="global-search-inner">
          {!result && !error && (
            <span className="search-hint">輸入台股代號查詢走勢</span>
          )}
          <input
            type="text"
            placeholder="股票代號，例如 2330"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            disabled={loading}
          />
          <button onClick={handleSearch} disabled={loading || !code.trim()}>
            {loading ? "查詢中..." : "查詢"}
          </button>
        </div>
      </div>

      {/* 主題內容 */}
      <div className="theme-content">
        <Suspense fallback={<div className="theme-loading">載入中...</div>}>
          {theme === "elderly" && <ElderlyTheme {...themeProps} />}
          {theme === "pro" && <ProTraderTheme {...themeProps} />}
          {theme === "beginner" && <BeginnerTheme {...themeProps} />}
        </Suspense>
      </div>
    </div>
  );
}

export default App;
