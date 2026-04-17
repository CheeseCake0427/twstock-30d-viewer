/**
 * 各主題 Recharts 圖表色票集中定義
 *
 * 為何不接 CSS variables：Recharts 把顏色以 SVG presentation attribute
 * 傳入（`stroke="..."` / `fill="..."`），瀏覽器不會解析 `var(--...)`。
 * 未來若要與 tokens.css 真正統一，做法是導入 `useChartColors` hook
 * 用 `getComputedStyle` 在 runtime 讀取——屬於後續 token 對齊 PR 範疇。
 *
 * 注意：Beginner 主題的 `.close-dot` / `.ma5-dot` / `.ma20-dot`（見
 * BeginnerTheme.css）目前仍硬編碼對應顏色，改色時記得兩邊同步。
 */

export type ChartColors = {
  /** Grid 線條顏色 */
  grid: string;
  /** 軸文字顏色（部份主題沿用 Recharts 預設） */
  axisText?: string;
  /** 軸線顏色（部份主題用不到） */
  axisLine?: string;
  /** 收盤價線 + dot */
  price: string;
  /** MA5 均線 */
  ma5: string;
  /** MA20 均線 */
  ma20: string;
  /** Reference line（AVG 基準線）— 目前僅 Pro 使用 */
  referenceLine?: string;
  /** Reference line 標籤文字 — 目前僅 Pro 使用 */
  referenceLabel?: string;
  /** Tooltip 背景 */
  tooltipBg?: string;
  /** Tooltip 邊框 */
  tooltipBorder?: string;
  /** Tooltip 內數值文字 */
  tooltipText?: string;
  /** Tooltip 日期標籤文字 */
  tooltipLabel?: string;
  /** Legend 文字顏色 */
  legendText?: string;
};

export const proChartColors: ChartColors = {
  grid: "#2a2d35",
  axisLine: "#2a2d35",
  axisText: "#8a8f98",
  referenceLine: "#444",
  referenceLabel: "#666",
  tooltipBg: "#1e2028",
  tooltipBorder: "#3a3d45",
  tooltipText: "#ccc",
  tooltipLabel: "#fff",
  legendText: "#8a8f98",
  price: "#4dabf7",
  ma5: "#ffd43b",
  ma20: "#ff6b6b",
};

export const beginnerChartColors: ChartColors = {
  grid: "#eee",
  axisText: "#888",
  tooltipBorder: "#e0e0e0",
  price: "#5b8def",
  ma5: "#f0a020",
  ma20: "#e05555",
};

export const elderlyChartColors: ChartColors = {
  grid: "#ddd",
  price: "#0066cc",
  ma5: "#e68a00",
  ma20: "#cc0000",
};
