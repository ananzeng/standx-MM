import logging

import requests

import config

logger = logging.getLogger(__name__)


def sendTelegram(text: str):
    if not config.telegramBotToken or not config.telegramChatId:
        return
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{config.telegramBotToken}/sendMessage",
            data={"chat_id": config.telegramChatId, "text": text},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.error("Telegram notify failed: %s", e)
