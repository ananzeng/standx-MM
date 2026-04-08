import os
from dotenv import load_dotenv

load_dotenv()

bscPrivateKey = os.getenv("BSC_PRIVATE_KEY", "")
bscAddress = os.getenv("BSC_ADDRESS", "")

symbol = os.getenv("SYMBOL", "BTC-USD")
orderSize = float(os.getenv("ORDER_SIZE", "0.001"))
spreadBps = float(os.getenv("SPREAD_BPS", "25"))
refreshInterval = int(os.getenv("REFRESH_INTERVAL", "10"))

uptimeEnabled = os.getenv("UPTIME_ENABLED", "false").lower() == "true"
uptimeSize = float(os.getenv("UPTIME_SIZE", "0.001"))
uptimeSpreadBps = float(os.getenv("UPTIME_SPREAD_BPS", "8"))

BASE_URL = "https://perps.standx.com"
AUTH_URL = "https://api.standx.com"
CHAIN = "bsc"
