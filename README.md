![Gurkerl Recommender MCP — Explainable grocery recommendations, with MCP integration.](docs/assets/banner.svg)

# Gurkerl Recommender MCP

Explainable grocery recommendations, with MCP integration.

[![CI](https://github.com/Fernise/gurkerl-recommender-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Fernise/gurkerl-recommender-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-52646b)](LICENSE)

Nutrition- and budget-aware grocery ranking, offer monitoring and weekly digests, with offline samples and optional MCP/Telegram integrations.

**Technology:** Python · SQLite · MCP · Optional Node.js bridge · Telegram

## What it does

- Explainable scoring for nutrition, price, promotions and close-to-expiry offers.
- A dependency-free sample recommender and configurable monitoring pipeline.
- Weekly plans/digests, notification deduplication and SQLite state.
- An optional local MCP server and clients for authenticated external MCP services.

## Project status

A personal recommendation toolkit with reproducible offline examples. External service ingestion and account tools require separate credentials and authorization. Recommendations do not provide medical nutrition advice or automatically place orders.

## Quick start

Requires Python 3.11+ for the documented setup; Node.js 22+ is needed only for the optional JavaScript bridge.

```sh
git clone https://github.com/Fernise/gurkerl-recommender-mcp.git
cd gurkerl-recommender-mcp
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m gurkerl_recommender.cli --sample
python -m gurkerl_recommender.monitor_cli --config config.example.json
```

The sample configuration is offline and prints to the console. To expose the local recommendation tools through MCP:

```sh
python -m pip install -e '.[mcp]'
python -m gurkerl_recommender.server
```

For the optional Node SDK helper, run `npm ci` first. See [configuration](docs/CONFIGURATION.md), [scoring](docs/scoring.md) and [MCP integration notes](docs/gurkerl-official-mcp.md). Real account credentials belong only in an ignored local `.env` file.

## Verification

```sh
python -m unittest discover -s tests -v
```

The suite uses sample products and mocked external responses. Authenticated grocery access, MCP account tools and Telegram delivery are not exercised during CI.

## Repository map

| Path | Responsibility |
| --- | --- |
| `gurkerl_recommender/` | Scoring, models, sources, MCP clients and CLI commands |
| `tests/` | Offline scoring, monitor, client and notifier regressions |
| `scripts/` | Optional Node MCP discovery helpers |
| `config*.example.json` | Safe source/notifier configuration examples |
| `profile.example.json` | Fictional recommendation preferences |
| `deploy/` | Example service/timer units |

## Documentation

- [Verification record and limits](docs/VERIFICATION.md)
- [Architecture and data boundaries](docs/ARCHITECTURE.md)
- [Configuration](docs/CONFIGURATION.md)
- [Security policy](SECURITY.md)
- [Contribution guidance](CONTRIBUTING.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## License

Original project code is licensed under the [MIT License](LICENSE).

Third-party libraries and assets retain their own licenses.
