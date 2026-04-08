import csv
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

ORDERS_FILE = "orders.csv"
TRADES_FILE = "trades.csv"

ORDERS_HEADER = ["time", "event", "side", "price", "mark_price", "spread_bps", "size", "order_id"]
TRADES_HEADER = ["fill_time", "close_time", "side", "entry_price", "exit_price", "size", "pnl_usd", "pnl_bps"]


def _ensureHeader(filePath: str, header: list):
    if not os.path.exists(filePath):
        with open(filePath, "w", newline="") as f:
            csv.writer(f).writerow(header)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _appendRow(filePath: str, row: list):
    with open(filePath, "a", newline="") as f:
        csv.writer(f).writerow(row)


class OrderTracker:
    def __init__(self):
        _ensureHeader(ORDERS_FILE, ORDERS_HEADER)
        _ensureHeader(TRADES_FILE, TRADES_HEADER)

    def recordPlace(self, orderId, side: str, price: float, markPrice: float, spreadBps: float, size: float):
        _appendRow(ORDERS_FILE, [_now(), "place", side, price, markPrice, spreadBps, size, orderId])

    def recordCancel(self, count: int):
        _appendRow(ORDERS_FILE, [_now(), "cancel_all", "", "", "", "", "", f"x{count}"])

    def recordFill(self, side: str, qty: float, entryPrice: float) -> dict:
        now = _now()
        _appendRow(ORDERS_FILE, [now, "filled", side, entryPrice, "", "", qty, ""])
        return {"fill_time": now, "side": side, "entry_price": entryPrice, "size": qty}

    def recordClose(self, fillInfo: dict, exitPrice: float):
        now = _now()
        side = fillInfo["side"]
        entryPrice = fillInfo["entry_price"]
        size = fillInfo["size"]

        if side == "buy":
            pnlUsd = (exitPrice - entryPrice) * size
        else:
            pnlUsd = (entryPrice - exitPrice) * size

        pnlBps = (pnlUsd / (entryPrice * size)) * 10000 if entryPrice * size > 0 else 0

        _appendRow(TRADES_FILE, [
            fillInfo["fill_time"], now, side, f"{entryPrice:.2f}",
            f"{exitPrice:.2f}", size, f"{pnlUsd:.4f}", f"{pnlBps:.2f}",
        ])

        logger.info("Trade closed: %s %s entry=%.2f exit=%.2f pnl=%.4f USD (%.2fbps)",
                     side, size, entryPrice, exitPrice, pnlUsd, pnlBps)

    def printStats(self):
        if not os.path.exists(TRADES_FILE):
            logger.info("No trades recorded yet")
            return

        totalTrades = 0
        totalPnl = 0.0
        wins = 0

        with open(TRADES_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                totalTrades += 1
                pnl = float(row["pnl_usd"])
                totalPnl += pnl
                if pnl >= 0:
                    wins += 1

        winRate = (wins / totalTrades * 100) if totalTrades > 0 else 0
        logger.info("=== Stats: %d trades | PnL: %.4f USD | Win rate: %.1f%% ===",
                     totalTrades, totalPnl, winRate)
