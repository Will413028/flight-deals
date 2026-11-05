# flight-deals

從桃園出發的便宜來回機票通知：定時查 Google Flights 各目的地未來 12 個月的最低價，比該目的地該月份 30 天中位數便宜 25% 以上時發 Telegram。

```sh
uv sync
export TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...
uv run flight-deals test-notify
uv run flight-deals run
```

目的地清單在 `src/flight_deals/destinations.py`，直接增刪。
