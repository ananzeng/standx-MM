# StandX Market Maker Bot

A low-risk market making bot for [StandX](https://standx.com) perpetual futures, designed to earn Maker Points and Uptime Program tokens by placing resting limit orders on both sides of the orderbook.

## How It Works

1. Fetches the current mark price for BTC-USD
2. Places dual-sided ALO (Add Liquidity Only) limit orders at a configurable spread
3. Refreshes orders every N seconds to track mark price movement
4. If an order gets filled, cancels all remaining orders and immediately market-closes the position
5. Logs all order and trade activity to CSV files

## Setup

```bash
cp .env.example .env
# Edit .env with your BSC wallet private key and address

python -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py
```

## Configuration

All parameters are set via `.env`:

| Variable | Default | Description |
|---|---|---|
| `BSC_PRIVATE_KEY` | — | BSC wallet private key |
| `BSC_ADDRESS` | — | BSC wallet address |
| `SYMBOL` | `BTC-USD` | Trading pair |
| `ORDER_SIZE` | `0.001` | Order size per side (BTC) |
| `SPREAD_BPS` | `25` | Distance from mark price in basis points |
| `REFRESH_INTERVAL` | `10` | Seconds between order refresh cycles |
| `UPTIME_ENABLED` | `false` | Enable tight-spread layer for Uptime Program |
| `UPTIME_SIZE` | `0.001` | Uptime layer order size |
| `UPTIME_SPREAD_BPS` | `8` | Uptime layer spread (must be within 10bps) |

## Output Files

- `orders.csv` — Every order placement, cancellation, and fill event
- `trades.csv` — Every fill-then-close cycle with PnL

## Strategy Overview

**Main Layer (default 25bps):** Low risk. Orders rarely get filled at this distance. Points accrue on resting orders even without execution.

**Uptime Layer (optional, 8bps):** Qualifies for the Maker Uptime Program (5M tokens/month). Requires both sides within 10bps and 30min uptime per hour. Higher fill risk but small size limits exposure.

## Risk

- Maker Points: Zero risk. Unfilled resting orders earn points.
- Filled orders: Cost per fill is ~6-8bps (1bp maker fee + 4bp taker fee + slippage).

## Project Structure

```
├── main.py           # Entry point
├── config.py         # Loads .env parameters
├── auth.py           # BSC wallet signing + JWT + ed25519 body signature
├── client.py         # StandX REST API client
├── strategy.py       # Core maker strategy logic
├── tracker.py        # CSV logging
├── .env.example      # Environment variable template
└── requirements.txt  # Python dependencies
```

---

# StandX 做市機器人

低風險做市機器人，用於 [StandX](https://standx.com) 永續合約交易所，透過在 orderbook 雙邊掛限價單來賺取 Maker Points 和 Uptime Program 代幣。

## 運作方式

1. 取得 BTC-USD 最新 mark price
2. 雙邊掛 ALO（Add Liquidity Only）限價單，距離可設定
3. 每 N 秒刷新掛單，跟著 mark price 移動
4. 被成交時，先取消所有掛單，再立刻市價平倉
5. 所有掛單和交易紀錄即時寫入 CSV

## 安裝

```bash
cp .env.example .env
# 編輯 .env，填入你的 BSC 錢包私鑰和地址

python -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py
```

## 設定參數

所有參數透過 `.env` 設定：

| 變數 | 預設值 | 說明 |
|---|---|---|
| `BSC_PRIVATE_KEY` | — | BSC 錢包私鑰 |
| `BSC_ADDRESS` | — | BSC 錢包地址 |
| `SYMBOL` | `BTC-USD` | 交易對 |
| `ORDER_SIZE` | `0.001` | 每邊掛單量（BTC） |
| `SPREAD_BPS` | `25` | 距離 mark price 的基點數 |
| `REFRESH_INTERVAL` | `10` | 掛單刷新間隔（秒） |
| `UPTIME_ENABLED` | `false` | 開啟窄 spread 層以參加 Uptime Program |
| `UPTIME_SIZE` | `0.001` | Uptime 層掛單量 |
| `UPTIME_SPREAD_BPS` | `8` | Uptime 層 spread（需在 10bps 內） |

## 輸出檔案

- `orders.csv` — 每筆掛單、取消、成交事件
- `trades.csv` — 每次成交後平倉的紀錄，含損益

## 策略說明

**主層（預設 25bps）：** 低風險。這個距離很少被成交，掛單在 orderbook 上超過 3 秒就持續累積積分。

**Uptime 層（選用，8bps）：** 符合 Maker Uptime Program 資格（每月 500 萬代幣）。需雙邊在 10bps 內，每小時至少 30 分鐘 uptime。被成交風險較高，但用小量控制曝險。

## 風險

- Maker Points：零風險，未成交的掛單也能拿積分
- 被成交：每次成本約 6-8bps（1bp maker fee + 4bp taker fee + 滑價）
