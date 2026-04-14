/**
 * 樂齡版主題元件測試。
 *
 * 對應 test-plan.md：
 *   - F-2 元件渲染測試
 */

import { describe } from "vitest";
import ElderlyTheme from "../../src/themes/ElderlyTheme";
import { runThemeTests } from "./helpers.js";

describe("ElderlyTheme", () => {
  runThemeTests("樂齡版", ElderlyTheme);
});
