import os

DATA_SOURCE = "twse"  # "seed" | "twse"
SEED_DIR = "../seed"

AI_API_KEY = os.environ.get("AI_API_KEY", "")  # 有值時啟用 AI 改寫模式，空字串則用模板模式

# 本地閒置自動關閉（分鐘）：> 0 才啟用，預設 0 即不啟用。
# 用途：本地測試後忘了停服務，避免長期佔用 port。
# 設定方式：環境變數 IDLE_SHUTDOWN_MINUTES=30 或直接修改本檔案。
IDLE_SHUTDOWN_MINUTES = int(os.environ.get("IDLE_SHUTDOWN_MINUTES", "0"))
