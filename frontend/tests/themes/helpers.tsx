/**
 * 主題測試共用工具。
 * 三套主題需要驗證相同的行為，這裡提供共用的測試邏輯。
 */

import { render, screen } from "@testing-library/react";
import type { ComponentType } from "react";
import type { ThemeProps } from "../../src/themes/types";
import type { StockResponse } from "../../src/types";

import successFixture from "../fixtures/success.json";
import withWarningsFixture from "../fixtures/with_warnings.json";
import errorFixture from "../fixtures/error.json";
import nullAnalysisFixture from "../fixtures/null_analysis.json";

// 載入 fixtures 並斷言型別
export const success = successFixture as unknown as StockResponse;
export const withWarnings = withWarningsFixture as unknown as StockResponse;
export const errorResponse = errorFixture as unknown as StockResponse;
export const nullAnalysis = nullAnalysisFixture as unknown as StockResponse;

/**
 * 為指定的主題元件執行所有 F-2 測試案例。
 */
export function runThemeTests(
  themeName: string,
  ThemeComponent: ComponentType<ThemeProps>,
) {
  describe(`${themeName} — F-2.1 正常資料渲染`, () => {
    it("顯示股票名稱與代號", () => {
      render(
        <ThemeComponent result={success} error={null} loading={false} />,
      );
      expect(screen.getByText(/9902/)).toBeTruthy();
      expect(screen.getByText(/測試股票B/)).toBeTruthy();
    });

    it("包含圖表元件（Recharts 容器存在）", () => {
      const { container } = render(
        <ThemeComponent result={success} error={null} loading={false} />,
      );
      // jsdom 下 ResponsiveContainer 不會渲染完整 SVG，改檢查容器 class
      const chart =
        container.querySelector(".recharts-responsive-container") ||
        container.querySelector("svg");
      expect(chart).not.toBeNull();
    });

    it("包含分析文字", () => {
      render(
        <ThemeComponent result={success} error={null} loading={false} />,
      );
      // success fixture 的 analysis 包含具體的漲幅數字
      const matches = screen.getAllByText(/8\.00%/);
      expect(matches.length).toBeGreaterThan(0);
    });

    it("分析區塊有 AI 生成標註", () => {
      render(
        <ThemeComponent result={success} error={null} loading={false} />,
      );
      // 各主題的標註文字可能不同，但都包含 "AI" 或 "ai"
      const aiLabels = screen.getAllByText(/AI/i);
      expect(aiLabels.length).toBeGreaterThan(0);
    });
  });

  describe(`${themeName} — F-2.2 警告顯示`, () => {
    it("顯示所有警告文字", () => {
      render(
        <ThemeComponent
          result={withWarnings}
          error={null}
          loading={false}
        />,
      );
      for (const w of withWarnings.warnings) {
        expect(screen.getByText(w)).toBeTruthy();
      }
    });

    it("多個 warnings 全部顯示", () => {
      render(
        <ThemeComponent
          result={withWarnings}
          error={null}
          loading={false}
        />,
      );
      const warningTexts = withWarnings.warnings.map((w) =>
        screen.getByText(w),
      );
      expect(warningTexts).toHaveLength(withWarnings.warnings.length);
    });

    it("無 warnings 時不顯示空的警告區塊", () => {
      const { container } = render(
        <ThemeComponent result={success} error={null} loading={false} />,
      );
      // Warnings 元件在 warnings=[] 時 return null
      // 各主題的 className 不同，但都不應出現 warnings 容器
      const warningBlocks = container.querySelectorAll(
        '[class*="warning"], [class*="Warning"]',
      );
      expect(warningBlocks).toHaveLength(0);
    });
  });

  describe(`${themeName} — F-2.3 錯誤狀態`, () => {
    it("顯示錯誤訊息", () => {
      render(
        <ThemeComponent
          result={null}
          error={errorResponse.error!}
          loading={false}
        />,
      );
      expect(screen.getByText(/查無此股票/)).toBeTruthy();
    });

    it("錯誤時不顯示圖表", () => {
      const { container } = render(
        <ThemeComponent
          result={null}
          error={errorResponse.error!}
          loading={false}
        />,
      );
      const svg = container.querySelector("svg");
      expect(svg).toBeNull();
    });

    it("analysis 為 null 時不顯示 'null' 文字", () => {
      render(
        <ThemeComponent
          result={nullAnalysis}
          error={null}
          loading={false}
        />,
      );
      // 畫面上不應出現文字 "null"
      const body = document.body.textContent ?? "";
      expect(body).not.toContain("null");
    });
  });
}
