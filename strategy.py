import logging
import time

from client import StandXClient
from tracker import OrderTracker
from notifier import sendTelegram
import config

logger = logging.getLogger(__name__)


class MakerStrategy:
    def __init__(self, client: StandXClient):
        self.client = client
        self.tracker = OrderTracker()
        self.lastMarkPrice = 0
        self.leverage = 10
        self.cooldownUntil = 0

    def run(self):
        logger.info(
            "Starting maker strategy: %s, size=%s, spread=%sbps, refresh=%ss",
            config.symbol, config.orderSize, config.spreadBps, config.refreshInterval,
        )
        if config.uptimeEnabled:
            logger.info(
                "Uptime layer enabled: size=%s, spread=%sbps",
                config.uptimeSize, config.uptimeSpreadBps,
            )
        self.client.login()

        try:
            posConfig = self.client.getPositionConfig(config.symbol)
            self.leverage = int(float(posConfig.get("leverage", 10)))
            logger.info("Current leverage: %dx", self.leverage)
        except Exception as e:
            logger.warning("Failed to get position config: %s, using default %dx", e, self.leverage)

        while True:
            try:
                self._tick()
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self._cancelAll()
                self.tracker.printStats()
                break
            except Exception as e:
                logger.error("Tick error: %s", e)

            time.sleep(config.refreshInterval)

    def _tick(self):
        hasPosition = self._checkAndClosePositions()
        if hasPosition:
            return
        self._refreshOrders()

    def _checkAndClosePositions(self) -> bool:
        positions = self.client.getPositions(config.symbol)
        for pos in positions:
            qty = float(pos.get("qty", 0))
            if qty == 0:
                continue

            entryPrice = float(pos.get("entry_price", 0))
            fillSide = "buy" if qty > 0 else "sell"
            closeSide = "sell" if qty > 0 else "buy"
            absQty = abs(qty)

            logger.info("Position detected: %s %s @ %.2f, cancelling all orders first",
                         fillSide, absQty, entryPrice)
            self._cancelAll()

            fillInfo = self.tracker.recordFill(fillSide, absQty, entryPrice)
            sendTelegram(f"🔔 Filled: {fillSide} {absQty} {config.symbol} @ {entryPrice:.2f}")
            self._closePosition(closeSide, absQty, fillInfo)
            self.cooldownUntil = time.time() + 300
            logger.info("Cooldown activated for 5 minutes (spread x2)")
            self.tracker.printStats()
            return True
        return False

    def _closePosition(self, closeSide: str, qty: float, fillInfo: dict):
        markPrice = self.client.getMarkPrice()
        limitPrice = round(markPrice, 2)
        logger.info("Attempting limit close: %s %s @ %.2f (30s timeout)", closeSide, qty, limitPrice)

        try:
            self.client.limitClose(closeSide, limitPrice, qty)
        except Exception as e:
            logger.error("Limit close failed: %s, falling back to market", e)
            self._marketCloseAndRecord(closeSide, qty, fillInfo)
            return

        deadline = time.time() + 30
        while time.time() < deadline:
            time.sleep(1)
            positions = self.client.getPositions(config.symbol)
            currentQty = 0
            for pos in positions:
                if abs(float(pos.get("qty", 0))) > 0:
                    currentQty = float(pos.get("qty", 0))
                    break

            if currentQty == 0:
                closePrice = self.client.getMarkPrice()
                logger.info("Limit close filled")
                closeInfo = self.tracker.recordClose(fillInfo, closePrice)
                sign = "+" if closeInfo["pnl_usd"] >= 0 else ""
                sendTelegram(
                    f"✅ Closed (limit): {closeSide} {qty} {config.symbol}\n"
                    f"entry={closeInfo['entry_price']:.2f} exit={closeInfo['exit_price']:.2f}\n"
                    f"PnL={sign}{closeInfo['pnl_usd']:.4f} USD ({sign}{closeInfo['pnl_bps']:.2f}bps)"
                )
                return

        logger.info("Limit close timeout, cancelling and using market order")
        self._cancelAll()
        self._marketCloseAndRecord(closeSide, qty, fillInfo)

    def _marketCloseAndRecord(self, closeSide: str, qty: float, fillInfo: dict):
        try:
            self.client.marketClose(closeSide, qty)
            closePrice = self.client.getMarkPrice()
            closeInfo = self.tracker.recordClose(fillInfo, closePrice)
            sign = "+" if closeInfo["pnl_usd"] >= 0 else ""
            sendTelegram(
                f"✅ Closed (market): {closeSide} {qty} {config.symbol}\n"
                f"entry={closeInfo['entry_price']:.2f} exit={closeInfo['exit_price']:.2f}\n"
                f"PnL={sign}{closeInfo['pnl_usd']:.4f} USD ({sign}{closeInfo['pnl_bps']:.2f}bps)"
            )
        except Exception as e:
            logger.error("Market close failed: %s", e)
            sendTelegram(f"❌ Market close failed: {e}")

    def _refreshOrders(self):
        self._cancelAll()

        markPrice = self.client.getMarkPrice()
        self.lastMarkPrice = markPrice

        mainSpreadBps = config.spreadBps
        if time.time() < self.cooldownUntil:
            mainSpreadBps = config.spreadBps * 2
            remaining = int(self.cooldownUntil - time.time())
            logger.info("Cooldown active (%ds left), main spread=%sbps", remaining, mainSpreadBps)

        self._placeLayer("main", markPrice, mainSpreadBps, config.orderSize)

        if config.uptimeEnabled:
            self._placeLayer("uptime", markPrice, config.uptimeSpreadBps, config.uptimeSize)

    def _placeLayer(self, label: str, markPrice: float, spreadBps: float, size: float):
        spread = markPrice * spreadBps / 10000
        bidPrice = round(markPrice - spread, 2)
        askPrice = round(markPrice + spread, 2)

        logger.info("[%s] Mark: %.2f | Bid: %.2f | Ask: %.2f | Spread: %.1fbps | Size: %s",
                     label, markPrice, bidPrice, askPrice, spreadBps, size)

        try:
            result = self.client.newOrder("buy", bidPrice, size)
            self.tracker.recordPlace(result.get("request_id"), "buy", bidPrice, markPrice, spreadBps, size, self.leverage)
        except Exception as e:
            logger.error("[%s] Failed to place bid: %s", label, e)

        try:
            result = self.client.newOrder("sell", askPrice, size)
            self.tracker.recordPlace(result.get("request_id"), "sell", askPrice, markPrice, spreadBps, size, self.leverage)
        except Exception as e:
            logger.error("[%s] Failed to place ask: %s", label, e)

    def _cancelAll(self):
        try:
            openOrders = self.client.getOpenOrders()
            orderIds = [o["id"] for o in openOrders if "id" in o]
            if orderIds:
                self.client.cancelOrders(orderIds)
                self.tracker.recordCancel(len(orderIds))
                logger.info("Cancelled %d orders", len(orderIds))
            else:
                logger.info("No open orders to cancel")
        except Exception as e:
            logger.error("Failed to cancel orders: %s", e)
