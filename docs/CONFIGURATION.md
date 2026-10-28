# Configuration

Start with `config.example.json`: it uses sample products, console output and local SQLite state. `profile.example.json` contains illustrative preferences only.

- `config.public.example.json` selects public offer pages and therefore makes network requests.
- `config.telegram.example.json` combines public sources with the Telegram notifier; it must be deliberately selected after private setup.
- `RHL_EMAIL` and `RHL_PASS` are optional private credentials for the external grocery MCP/account integration.
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` configure optional notifications.

Populate an ignored local `.env` only when needed. Store real profiles, account/order history and monitor state outside Git. Do not commit a config copied from a personal account.

## Package boundaries

`pip install -e .` installs the dependency-free recommendation/monitor core. `pip install -e '.[mcp]'` adds the optional Python MCP wrapper. Its FastMCP interface deliberately uses the v1 SDK (`mcp<2`); v2 renamed that API and is not silently selected. `npm ci` installs the separate Node SDK used by helpers in `scripts/`; it is not required for the sample recommender.

The local recommendation server exposes ranking tools. External MCP clients may have broader cart/account capabilities; review and authorize those separately. No checkout or purchase is performed by the offline sample or CI.

Deployment units under `deploy/` are examples. Supply your own service account, working directory and protected environment file; do not copy personal credentials into the unit file.
