# Notifications

The monitor is designed for proactive alerts:

```text
fetch product candidates
score them against your profile
notify only high-scoring matches
remember what was already notified
```

## Telegram Setup

1. In Telegram, open `@BotFather`.
2. Create a bot and copy its token.
3. Send a message to your new bot.
4. Get your chat id:

```bash
python3 -B -m gurkerl_recommender.telegram_cli get-updates
```

5. Add these values to `.env`:

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

6. In your real config file, set:

```json
{
  "notifier": {
    "type": "telegram"
  }
}
```

Then run:

```bash
python3 -B -m gurkerl_recommender.monitor_cli --config config.json
```

## VPS Cron

Run every three hours:

```cron
0 */3 * * * cd /path/to/gurkerl_mcp && python3 -B -m gurkerl_recommender.monitor_cli --config config.json
```

Start with a high `notification_threshold` such as `80` so alerts stay useful.
