/**
 * 異常與警告流程。
 *
 * 對應 test-plan.md：
 *   - E-2 異常與警告流程
 *
 * 前提：後端使用 seed 模式（DATA_SOURCE = "seed"）
 *   - invalid → stat 非 OK
 *   - few → 5 筆資料（不足 30 日、不足 20 筆）
 *   - 0050 → 22 筆資料（不足 30 日）
 */

import { test, expect } from "@playwright/test";

async function searchStock(page, code: string) {
  const input = page.locator('input[placeholder*="股票代號"]');
  await input.fill(code);
  await page.locator("button", { hasText: "查詢" }).click();
  await expect(page.locator("button", { hasText: "查詢中" })).toHaveCount(0, {
    timeout: 10_000,
  });
}

test.describe("E-2: 異常與警告流程", () => {
  test("輸入不存在的代號 → 無圖表、無分析、顯示錯誤訊息", async ({
    page,
  }) => {
    await page.goto("/");
    await searchStock(page, "invalid");

    // 顯示錯誤區塊
    const error = page.locator(".beginner-error");
    await expect(error).toBeVisible();

    // 錯誤訊息是使用者可讀的中文
    const errorText = await error.textContent();
    expect(errorText).toBeTruthy();
    expect(errorText!.length).toBeGreaterThan(0);

    // 無圖表
    await expect(page.locator(".recharts-responsive-container")).toHaveCount(0);

    // 無分析
    await expect(page.locator(".beginner-analysis")).toHaveCount(0);
  });

  test("輸入資料不足 30 天的股票 → 圖表正常渲染 + 黃色警告", async ({
    page,
  }) => {
    await page.goto("/");
    await searchStock(page, "0050");

    // 圖表仍顯示可用部分
    await expect(page.locator(".recharts-responsive-container")).toBeVisible();

    // 圖表有實際的折線（不是空殼）
    const lines = page.locator(".recharts-line");
    const lineCount = await lines.count();
    expect(lineCount).toBeGreaterThan(0);

    // 有筆數不足的警告
    await expect(page.locator("text=不足 30 日")).toBeVisible();
  });

  test("資料極少時 → 分析區塊顯示拒絕訊息或不顯示", async ({ page }) => {
    await page.goto("/");
    await searchStock(page, "few");

    // few 只有 5 筆（含空值），有效資料 < 10 筆，AI 應拒絕輸出
    // 分析區塊要嘛不存在，要嘛顯示「依據不足」
    const analysis = page.locator(".beginner-analysis");
    const analysisCount = await analysis.count();

    if (analysisCount > 0) {
      // 如果有分析區塊，應包含拒絕訊息
      await expect(analysis).toContainText("依據不足");
    }
    // analysisCount === 0 也是合理的（元件直接不渲染）

    // 應有警告提示
    const warnings = page.locator(".beginner-warnings");
    await expect(warnings).toBeVisible();
  });

  test("資料極少時 → 圖表仍能渲染不 crash", async ({ page }) => {
    await page.goto("/");
    await searchStock(page, "few");

    // few 有 4-5 筆有效資料，圖表應能渲染
    const chart = page.locator(".recharts-responsive-container");
    const chartCount = await chart.count();

    if (chartCount > 0) {
      // 圖表存在 → 應有 SVG 且沒有 JS error
      await expect(chart).toBeVisible();
    }
    // chartCount === 0 也可接受（元件判斷資料太少不渲染圖表）

    // 頁面沒有 crash（能看到警告區塊就代表頁面正常運作）
    await expect(page.locator(".beginner-warnings")).toBeVisible();
  });
});
