/**
 * 入門版主題元件測試。
 *
 * 對應 test-plan.md：
 *   - F-2 元件渲染測試
 */

import { describe } from "vitest";
import BeginnerTheme from "../../src/themes/BeginnerTheme";
import { runThemeTests } from "./helpers.js";

describe("BeginnerTheme", () => {
  runThemeTests("入門版", BeginnerTheme);
});
