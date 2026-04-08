import logging
import time

from client import StandXClient
from tracker import OrderTracker
import config

logger = logging.getLogger(__name__)


class MakerStrategy:
    def __init__(self, client: StandXClient):
        self.client = client
        self.tracker = OrderTracker()
        self.lastMarkPrice = 0

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

            try:
                self.client.marketClose(closeSide, absQty)
                closePrice = self.client.getMarkPrice()
                self.tracker.recordClose(fillInfo, closePrice)
            except Exception as e:
                logger.error("Failed to close position: %s", e)

            self.tracker.printStats()
            return True
        return False

    def _refreshOrders(self):
        self._cancelAll()

        markPrice = self.client.getMarkPrice()
        self.lastMarkPrice = markPrice

        self._placeLayer("main", markPrice, config.spreadBps, config.orderSize)

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
            self.tracker.recordPlace(result.get("request_id"), "buy", bidPrice, markPrice, spreadBps, size)
        except Exception as e:
            logger.error("[%s] Failed to place bid: %s", label, e)

        try:
            result = self.client.newOrder("sell", askPrice, size)
            self.tracker.recordPlace(result.get("request_id"), "sell", askPrice, markPrice, spreadBps, size)
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
