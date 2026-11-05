# flight-deals

Personal tool: alert on unusually cheap round-trip economy fares (≤ 1 stop) from TPE to the destinations in `src/flight_deals/destinations.py`, departing within the next 12 months.

## Commands (run from repo root; verified 2026-11-05)

- `uv sync` — install
- `uv run pytest -q` — unit tests (alert rules in `src/flight_deals/deal.py`)
- `uv run ruff check .` — lint
- `scripts/check.sh` — everything CI runs (needs gitleaks, osv-scanner on PATH); `scripts/install-hooks.sh` installs it as the pre-push hook, the only local gate since work goes straight to `main`
- `uv run flight-deals check-destinations` — every IATA code resolves in fli
- `uv run flight-deals run --dry-run --limit 3 --db /tmp/p.db` — live fetch, print alerts instead of sending
- `flight-deals run` / `test-notify` need `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`; `FLIGHT_DEALS_DB` sets the SQLite path

## Contracts and pitfalls

- Prices come from Google Flights' internal calendar endpoint through the `flights` package (fli), which reverse-engineers it; it is pinned. When fetches start failing for every destination, upgrade `flights` first. This scraping is against Google's terms; keep request volume low: the run sleeps 1–2 s between destinations and `fetch.py` sets fli's private `configure_concurrency(1)` so its 61-day chunks are fetched one at a time.
- The search window ends on a month boundary (`cli.search_window`); a rolling end date would grow the last month's series every day and fake price drops.
- `--dry-run` opens the store read-only: nothing it fetches or alerts is written, so it cannot suppress a real alert or pollute history.
- `flights` 0.9.0 imports `click` without declaring it, hence the explicit dependency.
- Alert rule (confirmed by Will): price ≤ 75% of the 30-day median of the same destination + departure month, only after ≥ 7 days of history; re-alert only after a further 5% drop. Tests in `tests/test_deal.py` encode each case.
- Never log Telegram request URLs: they contain the bot token.

## Storage and CI

- `.github/workflows/scrape.yml` runs every 3 hours and keeps history in `prices.sql` on the `data` branch. A `--db` path ending in `.sql` is a text dump (see `store.py`); rows older than 31 days are pruned each run, since no rule reads further back.
- Secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set by the owner with `gh secret set`; agents never handle their values.

## Supply chain

- Actions are pinned to full commit SHAs with the version in a trailing comment; workflows default to `contents: read`, and only the scrape job may write.
- `[tool.uv] exclude-newer = "7 days"` and Dependabot `cooldown` keep new releases out for 7 days.
- Agents do not add or upgrade dependencies on their own: list the package and version, confirm it exists and is not newly registered, and wait for the owner's approval.
- Fix deadlines for known vulnerabilities, from disclosure: critical 7 days, high 30 days, moderate or low at the next dependency update.
