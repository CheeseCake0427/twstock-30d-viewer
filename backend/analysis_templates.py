"""AI 分析模板定義。僅放文字模板，不含業務邏輯。"""

# --- 完整分析段落模板 ---
# 用於將多項事實串接為一段完整分析文字
FULL_ANALYSIS = "綜合近 {days} 個交易日資料，{facts_text}"

# --- 個別事實模板 ---

# 期間價格變化
PRICE_CHANGE_UP = (
    "收盤價從 {start_price} 元上漲至 {end_price} 元，漲幅 {change_pct}%"
)
PRICE_CHANGE_DOWN = (
    "收盤價從 {start_price} 元下跌至 {end_price} 元，跌幅 {change_pct}%"
)
PRICE_CHANGE_FLAT = (
    "收盤價從 {start_price} 元變動至 {end_price} 元，變動幅度 {change_pct}%"
)

# MA5 vs MA20 關係
MA_RELATION_ABOVE = (
    "MA5（{ma5} 元）高於 MA20（{ma20} 元），短期均線位於長期均線上方"
)
MA_RELATION_BELOW = (
    "MA5（{ma5} 元）低於 MA20（{ma20} 元），短期均線位於長期均線下方"
)
MA_RELATION_EQUAL = (
    "MA5（{ma5} 元）與 MA20（{ma20} 元）相近"
)

# MA 交叉事件
MA_CROSS_UP = "MA5 於 {date} 向上穿越 MA20"
MA_CROSS_DOWN = "MA5 於 {date} 向下穿越 MA20"

# 期間最高/最低價
PRICE_RANGE = (
    "期間最高價為 {high_price} 元（{high_date}），"
    "最低價為 {low_price} 元（{low_date}）"
)

# 近期趨勢
TREND_UP = "近 {n} 個交易日收盤價呈上升趨勢"
TREND_DOWN = "近 {n} 個交易日收盤價呈下降趨勢"
TREND_FLAT = "近 {n} 個交易日收盤價走勢持平"

# --- 拒絕輸出 ---
INSUFFICIENT_DATA = "依據不足，無法產生分析"

# --- AI 改寫用 prompt ---
AI_REWRITE_PROMPT = """請將以下關於股票的數據事實，改寫為一段流暢的繁體中文段落。

規則：
- 不可新增任何事實或數據
- 不可省略任何事實
- 不可提供投資建議、預測或主觀推薦
- 不可使用無法由以下事實直接支持的推論
- 語氣客觀中立

事實列表：
{facts_list}

請直接輸出改寫後的段落，不要加任何前綴或說明。"""

# --- AI 改寫後處理驗證用禁用詞 ---
BANNED_KEYWORDS = [
    "建議", "推薦", "值得", "看好", "看壞", "看漲", "看跌",
    "預期", "預計", "預測", "有望", "可能會",
    "買入", "賣出", "布局", "進場", "出場", "加碼", "減碼",
    "投資人", "股民", "散戶",
]
