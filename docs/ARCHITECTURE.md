# Gurkerl Recommender MCP — architecture

Nutrition- and budget-aware grocery ranking, offer monitoring and weekly digests, with offline samples and optional MCP/Telegram integrations.

## Code boundaries

- **gurkerl_recommender/:** Scoring, models, sources, MCP clients and CLI commands.
- **tests/:** Offline scoring, monitor, client and notifier regressions.
- **scripts/:** Optional Node MCP discovery helpers.
- **config*.example.json:** Safe source/notifier configuration examples.
- **profile.example.json:** Fictional recommendation preferences.
- **deploy/:** Example service/timer units.

## Data boundary

This public repository contains application source and fictional test inputs. Personal/operational state belongs in ignored local storage or separately configured services. Test results establish the behavior exercised by the suite; they do not certify live integrations, product efficacy or deployment readiness.

See the README for implementation status and `CONFIGURATION.md` for provider-specific requirements.
