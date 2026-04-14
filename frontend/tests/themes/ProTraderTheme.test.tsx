/**
 * 專業版主題元件測試。
 *
 * 對應 test-plan.md：
 *   - F-2 元件渲染測試
 */

import { describe } from "vitest";
import ProTraderTheme from "../../src/themes/ProTraderTheme";
import { runThemeTests } from "./helpers.js";

describe("ProTraderTheme", () => {
  runThemeTests("專業版", ProTraderTheme);
});
