/**
 * API 呼叫封裝測試。
 *
 * 對應 test-plan.md：
 *   - F-1 API 呼叫封裝
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchStock } from "../src/api";
import successFixture from "./fixtures/success.json";

// Mock global fetch
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

describe("F-1: fetchStock", () => {
  it("正常回應 → 回傳解析後的 JSON 物件", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(successFixture),
    });

    const result = await fetchStock("9902");
    expect(result.stock.code).toBe("9902");
    expect(result.data).toHaveLength(10);
    expect(result.analysis).toBeTruthy();
  });

  it("HTTP 錯誤（如 500）→ 拋出錯誤", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    await expect(fetchStock("9999")).rejects.toThrow("查詢失敗");
  });

  it("網路失敗 → 拋出錯誤", async () => {
    mockFetch.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    await expect(fetchStock("9999")).rejects.toThrow();
  });

  it("回傳結構符合 StockResponse 型別", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(successFixture),
    });

    const result = await fetchStock("9902");

    // stock
    expect(result).toHaveProperty("stock");
    expect(result.stock).toHaveProperty("code");
    expect(result.stock).toHaveProperty("name");

    // data array
    expect(Array.isArray(result.data)).toBe(true);
    const row = result.data[0];
    expect(row).toHaveProperty("date");
    expect(row).toHaveProperty("open");
    expect(row).toHaveProperty("high");
    expect(row).toHaveProperty("low");
    expect(row).toHaveProperty("close");
    expect(row).toHaveProperty("volume");
    expect(row).toHaveProperty("ma5");
    expect(row).toHaveProperty("ma20");

    // analysis, warnings
    expect(result).toHaveProperty("analysis");
    expect(result).toHaveProperty("warnings");
    expect(Array.isArray(result.warnings)).toBe(true);
  });
});
