import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { ThemeProps } from "./types";
import type { StockDayData } from "../types";
import Warnings from "../components/Warnings";
import { proChartColors as c } from "./chartColors";
import "./ProTraderTheme.css";

export default function ProTraderTheme({
  result,
  error,
  loading,
}: ThemeProps) {
  const data = result?.data ?? [];
  const last = data[data.length - 1];
  const prev = data[data.length - 2];
  const change = last && prev ? last.close - prev.close : null;
  const changePercent =
    change !== null && prev ? ((change / prev.close) * 100).toFixed(2) : null;

  // 統計數據
  const closes = data.map((d) => d.close).filter((c) => c > 0);
  const high30 = closes.length ? Math.max(...closes) : 0;
  const low30 = closes.length ? Math.min(...closes) : 0;
  const avgVol = data.length
    ? Math.round(data.reduce((s, d) => s + d.volume, 0) / data.length)
    : 0;

  return (
    <div className="pro">
      {/* 空狀態 */}
      {!result && !error && !loading && (
        <div className="pro-empty">
          <span className="pro-empty-logo">StockTerminal</span>
          <p>Enter ticker symbol above to begin</p>
        </div>
      )}

      {error && <div className="pro-error">{error}</div>}

      {result && data.length > 0 && (
        <div className="pro-grid">
          {/* 左側：價格資訊面板 */}
          <div className="pro-sidebar">
            <div className="pro-ticker">
              <span className="pro-code">{result.stock.code}</span>
              <span className="pro-name">{result.stock.name}</span>
            </div>

            {last && (
              <div className="pro-price-block">
                <div className="pro-current-price">
                  {last.close.toLocaleString()}
                </div>
                {change !== null && (
                  <div className={`pro-change ${change >= 0 ? "up" : "down"}`}>
                    {change >= 0 ? "+" : ""}
                    {change.toFixed(2)} ({changePercent}%)
                  </div>
                )}
              </div>
            )}

            <table className="pro-stats">
              <tbody>
                <tr>
                  <td>開</td>
                  <td>{last?.open.toLocaleString()}</td>
                  <td>高</td>
                  <td>{last?.high.toLocaleString()}</td>
                </tr>
                <tr>
                  <td>低</td>
                  <td>{last?.low.toLocaleString()}</td>
                  <td>量</td>
                  <td>{(last?.volume ?? 0).toLocaleString()}</td>
                </tr>
                <tr>
                  <td>MA5</td>
                  <td>{last?.ma5?.toFixed(2) ?? "—"}</td>
                  <td>MA20</td>
                  <td>{last?.ma20?.toFixed(2) ?? "—"}</td>
                </tr>
                <tr>
                  <td>30H</td>
                  <td>{high30.toLocaleString()}</td>
                  <td>30L</td>
                  <td>{low30.toLocaleString()}</td>
                </tr>
                <tr>
                  <td colSpan={2}>均量</td>
                  <td colSpan={2}>{avgVol.toLocaleString()}</td>
                </tr>
              </tbody>
            </table>

            {/* 警告 */}
            <Warnings warnings={result.warnings} className="pro-warnings" />

            {/* AI 分析 */}
            {result.analysis && (
              <div className="pro-analysis">
                <div className="pro-analysis-title">AI Analysis</div>
                <p>{result.analysis}</p>
                <span className="pro-ai-tag">AI Generated</span>
              </div>
            )}
          </div>

          {/* 右側：圖表 */}
          <div className="pro-chart-area">
            <ProChart data={data} />
            <ProTable data={data} />
          </div>
        </div>
      )}
    </div>
  );
}

function ProChart({ data }: { data: StockDayData[] }) {
  const closes = data.map((d) => d.close).filter((c) => c > 0);
  const min = Math.floor(Math.min(...closes) * 0.995);
  const max = Math.ceil(Math.max(...closes) * 1.005);
  const avg = closes.reduce((a, b) => a + b, 0) / closes.length;

  const chartData = data.map((d) => ({
    date: d.date.slice(5),
    close: d.close,
    ma5: d.ma5,
    ma20: d.ma20,
  }));

  return (
    <div className="pro-chart-scroll">
      <div className="pro-chart-inner">
        <ResponsiveContainer width="100%" height={380}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="2 2" stroke={c.grid} />
            <XAxis
              dataKey="date"
              tick={{ fill: c.axisText, fontSize: 11 }}
              axisLine={{ stroke: c.axisLine }}
              interval={2}
            />
            <YAxis
              domain={[min, max]}
              tick={{ fill: c.axisText, fontSize: 11 }}
              axisLine={{ stroke: c.axisLine }}
              width={70}
            />
            <ReferenceLine
              y={Math.round(avg)}
              stroke={c.referenceLine}
              strokeDasharray="3 3"
              label={{
                value: `AVG ${Math.round(avg)}`,
                fill: c.referenceLabel,
                fontSize: 10,
              }}
            />
            <Tooltip
              contentStyle={{
                background: c.tooltipBg,
                border: `1px solid ${c.tooltipBorder}`,
                borderRadius: 4,
                fontSize: 12,
              }}
              itemStyle={{ color: c.tooltipText }}
              labelStyle={{ color: c.tooltipLabel }}
              formatter={(v, name) => [
                typeof v === "number" ? v.toFixed(2) : "—",
                name === "close" ? "Close" : String(name).toUpperCase(),
              ]}
            />
            <Legend
              wrapperStyle={{ fontSize: 11, color: c.legendText }}
              formatter={(v) => (v === "close" ? "CLOSE" : v.toUpperCase())}
            />
            <Line
              type="monotone"
              dataKey="close"
              stroke={c.price}
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 3, fill: c.price }}
            />
            <Line
              type="monotone"
              dataKey="ma5"
              stroke={c.ma5}
              strokeWidth={1}
              dot={false}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="ma20"
              stroke={c.ma20}
              strokeWidth={1}
              dot={false}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ProTable({ data }: { data: StockDayData[] }) {
  // 顯示最近 10 筆
  const recent = data.slice(-10).reverse();

  return (
    <div className="pro-table-wrap">
      <table className="pro-table">
        <thead>
          <tr>
            <th>日期</th>
            <th>開盤</th>
            <th>最高</th>
            <th>最低</th>
            <th>收盤</th>
            <th>MA5</th>
            <th>MA20</th>
            <th>成交量</th>
          </tr>
        </thead>
        <tbody>
          {recent.map((d) => (
            <tr key={d.date}>
              <td>{d.date.slice(5)}</td>
              <td>{d.open.toLocaleString()}</td>
              <td>{d.high.toLocaleString()}</td>
              <td>{d.low.toLocaleString()}</td>
              <td>{d.close.toLocaleString()}</td>
              <td>{d.ma5?.toFixed(2) ?? "—"}</td>
              <td>{d.ma20?.toFixed(2) ?? "—"}</td>
              <td>{(d.volume / 1000).toFixed(0)}K</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
