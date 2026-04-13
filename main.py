import logging
import os
from datetime import datetime, timezone, timedelta

from client import StandXClient
from strategy import MakerStrategy

LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)
TZ_UTC8 = timezone(timedelta(hours=8))
logFile = os.path.join(LOG_DIR, datetime.now(TZ_UTC8).strftime("%Y-%m-%d") + ".txt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(logFile, mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

if __name__ == "__main__":
    client = StandXClient()
    strategy = MakerStrategy(client)
    strategy.run()
