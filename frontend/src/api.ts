import type { StockResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export async function fetchStock(code: string): Promise<StockResponse> {
  const res = await fetch(`${API_BASE}/api/stock/${code}`);
  if (!res.ok) {
    throw new Error(`查詢失敗 (${res.status})`);
  }
  return res.json();
}
