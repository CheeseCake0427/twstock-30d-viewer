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
import { elderlyChartColors as c } from "./chartColors";
import "./ElderlyTheme.css";

export default function ElderlyTheme({
  result,
  error,
  loading,
}: ThemeProps) {
  const data = result?.data ?? [];
  const lastDay = data[data.length - 1];
  const prevDay = data[data.length - 2];
  const priceChange =
    lastDay && prevDay ? lastDay.close - prevDay.close : null;

  return (
    <div className="elderly">
      {/* 空狀態 */}
      {!result && !error && !loading && (
        <div className="elderly-empty">
          <h1>股票查詢</h1>
          <p>在上方輸入代號，查看近期走勢</p>
        </div>
      )}

      {error && <div className="elderly-error">{error}</div>}

      {result && data.length > 0 && (
        <div className="elderly-layout">
          {/* 左欄：價格 + 均線 + 警告 + AI 分析 */}
          <div className="elderly-sidebar">
            {/* 大字價格卡片 */}
            <div className="elderly-price-card">
              <div className="elderly-stock-name">
                {result.stock.code} {result.stock.name}
              </div>
              {lastDay && (
                <>
                  <div className="elderly-price">
                    {lastDay.close.toLocaleString()}
                  </div>
                  <div className="elderly-unit">元（最新收盤價）</div>
                  {priceChange !== null && (
                    <div
                      className={`elderly-change ${priceChange >= 0 ? "up" : "down"}`}
                    >
                      {priceChange >= 0 ? "▲ 漲" : "▼ 跌"}{" "}
                      {Math.abs(priceChange).toFixed(2)} 元
                    </div>
                  )}
                </>
              )}
            </div>

            {/* 均線資訊卡 */}
            {lastDay && (
              <div className="elderly-ma-cards">
                <div className="elderly-ma-card">
                  <div className="elderly-ma-label">5 日均線</div>
                  <div className="elderly-ma-value">
                    {lastDay.ma5 !== null
                      ? `${lastDay.ma5.toLocaleString()} 元`
                      : "資料不足"}
                  </div>
                  <div className="elderly-ma-explain">
                    近 5 天收盤價的平均
                  </div>
                </div>
                <div className="elderly-ma-card">
                  <div className="elderly-ma-label">20 日均線</div>
                  <div className="elderly-ma-value">
                    {lastDay.ma20 !== null
                      ? `${lastDay.ma20.toLocaleString()} 元`
                      : "資料不足"}
                  </div>
                  <div className="elderly-ma-explain">
                    近 20 天收盤價的平均
                  </div>
                </div>
              </div>
            )}

            {/* 警告 */}
            <Warnings warnings={result.warnings} className="elderly-warnings" />

            {/* AI 分析 */}
            {result.analysis && (
              <div className="elderly-analysis">
                <h2>分析摘要</h2>
                <p>{result.analysis}</p>
                <p className="elderly-disclaimer">＊ 以上為 AI 生成內容</p>
              </div>
            )}
          </div>

          {/* 右欄：走勢圖 */}
          <div className="elderly-main">
            <div className="elderly-chart">
              <h2>股價走勢圖</h2>
              <ElderlyChart data={data} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ElderlyChart({ data }: { data: StockDayData[] }) {
  const closes = data.map((d) => d.close).filter((c) => c > 0);
  const min = Math.floor(Math.min(...closes) * 0.99);
  const max = Math.ceil(Math.max(...closes) * 1.01);

  const chartData = data.map((d) => ({
    date: d.date.slice(5),
    close: d.close,
    ma5: d.ma5,
    ma20: d.ma20,
  }));

  return (
    <ResponsiveContainer width="100%" height={420}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="4 4" stroke={c.grid} />
        <XAxis dataKey="date" tick={{ fontSize: 16 }} interval={4} />
        <YAxis domain={[min, max]} tick={{ fontSize: 16 }} width={80} />
        <Tooltip
          contentStyle={{ fontSize: 18, borderRadius: 10 }}
          formatter={(v, name) => [
            `${typeof v === "number" ? v.toFixed(2) : "—"} 元`,
            name === "close" ? "收盤價" : name === "ma5" ? "5日均線" : "20日均線",
          ]}
          labelFormatter={(l) => `日期：${l}`}
        />
        <Legend
          wrapperStyle={{ fontSize: 18 }}
          formatter={(v) =>
            v === "close" ? "收盤價" : v === "ma5" ? "5日均線" : "20日均線"
          }
        />
        <Line
          type="monotone"
          dataKey="close"
          stroke={c.price}
          strokeWidth={3}
          dot={{ r: 3 }}
        />
        <Line
          type="monotone"
          dataKey="ma5"
          stroke={c.ma5}
          strokeWidth={2.5}
          dot={false}
          connectNulls={false}
        />
        <Line
          type="monotone"
          dataKey="ma20"
          stroke={c.ma20}
          strokeWidth={2.5}
          dot={false}
          connectNulls={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
