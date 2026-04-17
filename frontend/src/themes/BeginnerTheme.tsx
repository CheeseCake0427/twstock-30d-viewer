import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ThemeProps } from "./types";
import type { StockDayData } from "../types";
import Warnings from "../components/Warnings";
import { beginnerChartColors as c } from "./chartColors";
import "./BeginnerTheme.css";

export default function BeginnerTheme({
  result,
  error,
  loading,
}: ThemeProps) {
  const data = result?.data ?? [];
  const last = data[data.length - 1];
  const first = data[0];
  const totalChange = last && first ? last.close - first.close : null;
  const totalChangePercent =
    totalChange !== null && first
      ? ((totalChange / first.close) * 100).toFixed(2)
      : null;

  return (
    <div className="beginner">
      {/* 空狀態引導 */}
      {!result && !error && !loading && (
        <div className="beginner-empty">
          <h2>歡迎使用股票小幫手</h2>
          <p>在上方搜尋列輸入股票代號，開始查看走勢</p>
          <p className="beginner-hint">
            不知道代號？試試看 2330（台積電）、0050（台灣50 ETF）
          </p>
        </div>
      )}

      {error && (
        <div className="beginner-error">
          <span className="beginner-error-icon">!</span>
          <div>
            <strong>查詢失敗</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {result && data.length > 0 && (
        <div className="beginner-layout">
          {/* 左欄：摘要卡片 + 警告 + AI 分析 */}
          <div className="beginner-sidebar">
            <div className="beginner-card main-card">
              <div className="beginner-card-label">
                {result.stock.code} {result.stock.name}
              </div>
              <div className="beginner-card-value">
                {last?.close.toLocaleString()}
                <span className="beginner-card-unit">元</span>
              </div>
              <div className="beginner-card-sub">最新收盤價</div>
            </div>

            <div
              className={`beginner-card ${totalChange !== null && totalChange >= 0 ? "card-up" : "card-down"}`}
            >
              <div className="beginner-card-label">
                近 {data.length} 天變化
              </div>
              <div className="beginner-card-value">
                {totalChange !== null
                  ? `${totalChange >= 0 ? "+" : ""}${totalChange.toFixed(2)}`
                  : "—"}
              </div>
              <div className="beginner-card-sub">
                {totalChangePercent
                  ? `${Number(totalChangePercent) >= 0 ? "上漲" : "下跌"} ${Math.abs(Number(totalChangePercent))}%`
                  : ""}
              </div>
            </div>

            <div className="beginner-card-row">
              <div className="beginner-card">
                <div className="beginner-card-label">5 日均線 (MA5)</div>
                <div className="beginner-card-value">
                  {last?.ma5?.toLocaleString() ?? "—"}
                </div>
                <div className="beginner-card-sub beginner-tooltip">
                  近 5 天收盤價的平均值
                </div>
              </div>

              <div className="beginner-card">
                <div className="beginner-card-label">20 日均線 (MA20)</div>
                <div className="beginner-card-value">
                  {last?.ma20?.toLocaleString() ?? "—"}
                </div>
                <div className="beginner-card-sub beginner-tooltip">
                  近 20 天收盤價的平均值
                </div>
              </div>
            </div>

            {/* 警告 */}
            <Warnings warnings={result.warnings} className="beginner-warnings" title="提醒事項" />

            {/* AI 分析 */}
            {result.analysis && (
              <div className="beginner-analysis">
                <h2>AI 幫你看</h2>
                <p className="beginner-analysis-text">{result.analysis}</p>
                <div className="beginner-ai-badge">AI 生成內容，僅供參考</div>
              </div>
            )}

          </div>

          {/* 右欄：圖表 + 名詞小教室 */}
          <div className="beginner-main">
            <div className="beginner-chart-section">
              <h2>股價走勢圖</h2>
              <div className="beginner-legend-explain">
                <span className="legend-dot close-dot" />{" "}
                <strong>收盤價</strong>：每天收盤時的價格 &nbsp;&nbsp;
                <span className="legend-dot ma5-dot" /> <strong>MA5</strong>
                ：近 5 天平均 &nbsp;&nbsp;
                <span className="legend-dot ma20-dot" /> <strong>MA20</strong>
                ：近 20 天平均
              </div>
              <BeginnerChart data={data} />
            </div>

            {/* 名詞小教室 */}
            <Glossary />
          </div>
        </div>
      )}
    </div>
  );
}

const glossaryItems = [
  {
    term: "股票代號",
    desc: "每檔股票在交易所的編號，例如 2330 是台積電。上市股票通常是 4 碼數字，0050 這類是 ETF。輸入代號就能查到對應的公司。",
  },
  {
    term: "收盤價",
    desc: "當天股市收盤（下午 1:30）時最後的成交價格。因為股價隨時在變，收盤價是大家最常拿來比較「今天漲還是跌」的基準。",
  },
  {
    term: "漲 / 跌（紅與綠）",
    desc: "台股慣例：紅色代表上漲、綠色代表下跌，跟歐美股市剛好相反。畫面上看到紅色表示價格比之前高，綠色表示變低了。",
  },
  {
    term: "均線（MA5 / MA20）",
    desc: "把最近幾天的收盤價加起來除以天數，就是「移動平均線」。MA5 是最近 5 天的平均，反映短期趨勢；MA20 是 20 天的平均，反映中期趨勢。當短期均線往上穿過長期均線，通常被認為是上漲訊號，反之則是下跌訊號。",
  },
  {
    term: "走勢圖怎麼看",
    desc: "橫軸是日期、縱軸是價格。藍色實線是每天的收盤價，虛線是均線。線往右上走代表最近在漲，往右下走代表在跌。把滑鼠移到線上可以看到當天的數字。",
  },
  {
    term: "ETF",
    desc: "一種可以像股票一樣買賣的基金，一次買進一籃子股票。例如 0050 包含台灣市值最大的 50 家公司，適合不想挑個股的新手分散風險。",
  },
];

function Glossary() {
  const [open, setOpen] = useState(false);

  return (
    <div className="beginner-glossary">
      <button
        className="beginner-glossary-toggle"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="beginner-glossary-icon">📖</span>
        名詞小教室
        <span className={`beginner-glossary-arrow ${open ? "open" : ""}`}>
          ▾
        </span>
      </button>
      {open && (
        <dl className="beginner-glossary-list">
          {glossaryItems.map((item) => (
            <div className="beginner-glossary-item" key={item.term}>
              <dt>{item.term}</dt>
              <dd>{item.desc}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

function BeginnerChart({ data }: { data: StockDayData[] }) {
  const closes = data.map((d) => d.close).filter((c) => c > 0);
  const min = Math.floor(Math.min(...closes) * 0.995);
  const max = Math.ceil(Math.max(...closes) * 1.005);

  const chartData = data.map((d) => ({
    date: d.date.slice(5),
    close: d.close,
    ma5: d.ma5,
    ma20: d.ma20,
  }));

  return (
    <div className="beginner-chart-scroll-frame">
      <div className="beginner-chart-scroll">
        <div className="beginner-chart-inner">
          <ResponsiveContainer width="100%" height={420}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke={c.grid} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12, fill: c.axisText }}
                interval={3}
              />
              <YAxis
                domain={[min, max]}
                tick={{ fontSize: 12, fill: c.axisText }}
                width={70}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: 8,
                  fontSize: 13,
                  border: `1px solid ${c.tooltipBorder}`,
                }}
                formatter={(v, name) => [
                  `${typeof v === "number" ? v.toFixed(2) : "—"} 元`,
                  name === "close"
                    ? "收盤價"
                    : name === "ma5"
                      ? "5日均線"
                      : "20日均線",
                ]}
                labelFormatter={(l) => `${l}`}
              />
              <Legend
                formatter={(v) =>
                  v === "close"
                    ? "收盤價"
                    : v === "ma5"
                      ? "MA5 均線"
                      : "MA20 均線"
                }
              />
              <Line
                type="monotone"
                dataKey="close"
                stroke={c.price}
                strokeWidth={2.5}
                dot={{ r: 2.5, fill: c.price }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="ma5"
                stroke={c.ma5}
                strokeWidth={2}
                strokeDasharray="6 3"
                dot={false}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="ma20"
                stroke={c.ma20}
                strokeWidth={2}
                strokeDasharray="6 3"
                dot={false}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
