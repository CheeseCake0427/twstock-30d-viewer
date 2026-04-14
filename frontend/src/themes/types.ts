import type { StockResponse } from "../types";

export interface ThemeProps {
  result: StockResponse | null;
  error: string | null;
  loading: boolean;
}
