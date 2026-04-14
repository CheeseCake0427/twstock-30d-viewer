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
import type { StockDayData } from "../types";

interface Props {
  data: StockDayData[];
  stockName: string;
}

export default function StockChart({ data, stockName }: Props) {
  if (data.length === 0) return null;

  // 計算 Y 軸範圍：取所有價格的最小/最大值，留一點邊距
  const allPrices = data.flatMap((d) => [
    d.close,
    d.ma5 ?? Infinity,
    d.ma20 ?? Infinity,
  ]);
  const validPrices = allPrices.filter((p) => p !== Infinity && p > 0);
  const minPrice = Math.floor(Math.min(...validPrices) * 0.995);
  const maxPrice = Math.ceil(Math.max(...validPrices) * 1.005);

  // 格式化日期：只顯示 MM/DD
  const chartData = data.map((d) => ({
    ...d,
    shortDate: d.date.slice(5), // "2026-03-02" → "03-02"
  }));

  return (
    <div className="chart-container">
      <h3>{stockName} 股價走勢圖</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="shortDate"
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
          />
          <YAxis domain={[minPrice, maxPrice]} tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value, name) => {
              const label =
                name === "close"
                  ? "收盤價"
                  : name === "ma5"
                    ? "MA5"
                    : "MA20";
              return [typeof value === "number" ? value.toFixed(2) : "—", label];
            }}
            labelFormatter={(label) => `日期：${label}`}
          />
          <Legend
            formatter={(value) =>
              value === "close"
                ? "收盤價"
                : value === "ma5"
                  ? "MA5"
                  : "MA20"
            }
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#1677ff"
            strokeWidth={2}
            dot={{ r: 2 }}
            activeDot={{ r: 5 }}
          />
          <Line
            type="monotone"
            dataKey="ma5"
            stroke="#f5a623"
            strokeWidth={1.5}
            dot={false}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="ma20"
            stroke="#e74c3c"
            strokeWidth={1.5}
            dot={false}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
