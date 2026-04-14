export interface StockDayData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ma5: number | null;
  ma20: number | null;
}

export interface StockInfo {
  code: string;
  name: string;
}

export interface ExtraInfo {
  pe_ratio: string | null;
  dividend_yield: string | null;
  pb_ratio: string | null;
}

export interface StockResponse {
  stock: StockInfo;
  data: StockDayData[];
  analysis: string | null;
  warnings: string[];
  extra: ExtraInfo | null;
  error?: string;
}
