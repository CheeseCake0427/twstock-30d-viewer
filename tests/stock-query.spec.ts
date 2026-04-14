/**
 * 正常查詢流程 + 連續操作。
 *
 * 對應 test-plan.md：
 *   - E-1 正常查詢流程
 *   - E-3 連續操作
 *
 * 前提：後端使用 seed 模式（DATA_SOURCE = "seed"）
 *   - 2330 → 36 筆完整資料（截取 30 筆）
 *   - 0050 → 22 筆資料（不足 30 日）
 */

import { test, expect } from "@playwright/test";

// 共用的搜尋操作
async function searchStock(page, code: string) {
  const input = page.locator('input[placeholder*="股票代號"]');
  await input.fill(code);
  await page.locator("button", { hasText: "查詢" }).click();
  // 等待查詢完成（按鈕從「查詢中...」變回「查詢」）
  await expect(page.locator("button", { hasText: "查詢中" })).toHaveCount(0, {
    timeout: 10_000,
  });
}

// ============================================================
// E-1: 正常查詢流程
// ============================================================

test.describe("E-1: 正常查詢流程", () => {
  test("輸入 2330 → 看到走勢圖", async ({ page }) => {
    await page.goto("/");
    await searchStock(page, "2330");

    // 圖表容器存在
    const chart = page.locator(".recharts-responsive-container");
    await expect(chart).toBeVisible();

    // 主圖表 SVG（role="application" 是 Recharts 主圖表，排除 legend 小 icon）
    const svg = page.locator('.recharts-responsive-container svg[role="application"]');
    await expect(svg).toBeVisible();

    // 三條線可辨識：收盤價 + MA5 + MA20（Recharts 的 .recharts-line）
    const lines = page.locator(".recharts-line");
    await expect(lines).toHaveCount(3);
  });

  test("輸入 2330 → 看到 AI 分析文字", async ({ page }) => {
    await page.goto("/");
    await searchStock(page, "2330");

    // 分析區塊存在（入門版的 class）
    const analysis = page.locator(".beginner-analysis");
    await expect(analysis).toBeVisible();

    // 分析文字包含具體數字（非空內容）
    const text = await analysis.locator(".beginner-analysis-text").textContent();
    expect(text).toBeTruthy();
    expect(text!.length).toBeGreaterThan(10);

    // 有 AI 生成標註
    await expect(analysis.locator(".beginner-ai-badge")).toBeVisible();
  });

  test("滑鼠懸停圖表 → tooltip 顯示當日數值", async ({ page }) => {
    await page.goto("/");
    await searchStock(page, "2330");

    // 找到主圖表 SVG 並 hover
    const chartArea = page.locator('.recharts-responsive-container svg[role="application"]');
    await expect(chartArea).toBeVisible();

    // 移動到圖表中央觸發 tooltip
    const box = await chartArea.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    }

    // tooltip 應該出現，Recharts 用 .recharts-tooltip-wrapper
    const tooltip = page.locator(".recharts-tooltip-wrapper");
    // tooltip 可能需要一點時間出現
    await expect(tooltip).toBeAttached({ timeout: 3000 });
  });

  test("tooltip 在 MA 為 null 的日期不顯示 null 或 NaN", async ({ page }) => {
    await page.goto("/");
    await searchStock(page, "2330");

    const chartArea = page.locator(
      '.recharts-responsive-container svg[role="application"]',
    );
    await expect(chartArea).toBeVisible();

    const box = await chartArea.boundingBox();
    if (!box) return;

    // hover 到圖表最左側（前幾天 MA5/MA20 為 null）
    await page.mouse.move(box.x + box.width * 0.05, box.y + box.height / 2);

    const tooltip = page.locator(".recharts-tooltip-wrapper");
    await expect(tooltip).toBeAttached({ timeout: 3000 });

    const tooltipText = await tooltip.textContent();
    expect(tooltipText).not.toContain("null");
    expect(tooltipText).not.toContain("NaN");
    expect(tooltipText).not.toContain("undefined");
  });
});

// ============================================================
// E-3: 連續操作
// ============================================================

test.describe("E-3: 連續操作", () => {
  test("查詢 A 後再查詢 B → 畫面完全更新", async ({ page }) => {
    await page.goto("/");

    // 先查 2330
    await searchStock(page, "2330");
    await expect(page.locator("text=2330")).toBeVisible();
    const analysisA = await page
      .locator(".beginner-analysis-text")
      .textContent();

    // 再查 0050
    await searchStock(page, "0050");

    // 畫面應顯示 0050，不殘留 2330
    await expect(page.locator(".beginner-card-label >> text=0050")).toBeVisible();

    // 因為 0050 僅 22 筆，應有不足 30 日的警告
    await expect(page.locator("text=不足 30 日")).toBeVisible();

    // 分析文字應該變了（或因不足而消失）
    const analysisB = page.locator(".beginner-analysis-text");
    const hasBAnalysis = (await analysisB.count()) > 0;
    if (hasBAnalysis) {
      const textB = await analysisB.textContent();
      // 如果兩邊都有分析，文字應不同
      expect(textB).not.toBe(analysisA);
    }
  });

  test("查詢成功後再查詢無效代號 → 顯示錯誤", async ({ page }) => {
    await page.goto("/");

    // 先查成功的 2330
    await searchStock(page, "2330");
    await expect(page.locator(".beginner-analysis")).toBeVisible();

    // 再查無效代號
    await searchStock(page, "invalid");

    // 之前的結果應被清除
    await expect(page.locator(".beginner-analysis")).toHaveCount(0);

    // 應顯示錯誤訊息
    await expect(page.locator(".beginner-error")).toBeVisible();
  });
});
