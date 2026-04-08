import logging

import requests

from auth import StandXAuth
import config

logger = logging.getLogger(__name__)


class StandXClient:
    def __init__(self):
        self.auth = StandXAuth()
        self.baseUrl = config.BASE_URL

    def login(self):
        self.auth.login()

    def getMarkPrice(self, symbol: str = None) -> float:
        symbol = symbol or config.symbol
        resp = requests.get(
            f"{self.baseUrl}/api/query_symbol_price",
            params={"symbol": symbol},
            timeout=10,
        )
        resp.raise_for_status()
        return float(resp.json()["mark_price"])

    def getSymbolInfo(self, symbol: str = None) -> dict:
        symbol = symbol or config.symbol
        resp = requests.get(
            f"{self.baseUrl}/api/query_symbol_info",
            params={"symbol": symbol},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def _signedPost(self, path: str, payload: dict) -> requests.Response:
        headers, body = self.auth.getSignedRequest(payload)
        resp = requests.post(
            f"{self.baseUrl}{path}",
            headers=headers,
            data=body,
            timeout=10,
        )
        if resp.status_code != 200:
            logger.error("%s failed [%d]: %s", path, resp.status_code, resp.text)
        resp.raise_for_status()
        return resp

    def newOrder(self, side: str, price: float, qty: float, symbol: str = None) -> dict:
        symbol = symbol or config.symbol
        payload = {
            "symbol": symbol,
            "side": side,
            "order_type": "limit",
            "qty": str(qty),
            "price": str(price),
            "time_in_force": "alo",
            "reduce_only": False,
        }
        result = self._signedPost("/api/new_order", payload).json()
        logger.info("Order placed: %s %s @ %s (%s) response=%s", side, qty, price, symbol, result)
        return result

    def marketClose(self, side: str, qty: float, symbol: str = None) -> dict:
        symbol = symbol or config.symbol
        payload = {
            "symbol": symbol,
            "side": side,
            "order_type": "market",
            "qty": str(qty),
            "time_in_force": "ioc",
            "reduce_only": True,
        }
        result = self._signedPost("/api/new_order", payload).json()
        logger.info("Market close: %s %s (%s)", side, qty, symbol)
        return result

    def cancelOrder(self, orderId: int) -> dict:
        return self._signedPost("/api/cancel_order", {"order_id": orderId}).json()

    def cancelOrders(self, orderIds: list) -> dict:
        if not orderIds:
            return {}
        return self._signedPost("/api/cancel_orders", {"order_id_list": orderIds}).json()

    def getOpenOrders(self, symbol: str = None) -> list:
        symbol = symbol or config.symbol
        resp = requests.get(
            f"{self.baseUrl}/api/query_open_orders",
            params={"symbol": symbol},
            headers=self.auth.getHeaders(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        logger.debug("query_open_orders raw response: %s", data)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("rows", "orders", "data", "result"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []

    def getPositions(self, symbol: str = None) -> list:
        params = {}
        if symbol:
            params["symbol"] = symbol
        resp = requests.get(
            f"{self.baseUrl}/api/query_positions",
            params=params,
            headers=self.auth.getHeaders(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        logger.debug("query_positions raw: %s", data)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("rows", "positions", "data", "result"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []
