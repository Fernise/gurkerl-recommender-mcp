# Gurkerl Official MCP

Gurkerl publishes an official remote MCP server:

```text
https://mcp.gurkerl.at/mcp/
```

The current Gurkerl docs describe OAuth as the preferred setup:

```bash
claude mcp add --transport http gurkerl-mcp https://mcp.gurkerl.at/mcp
```

Then run `/mcp`, choose `gurkerl-mcp`, and authenticate in the browser.

For Claude Desktop / ChatGPT, Gurkerl says to add a custom connector with:

```text
https://mcp.gurkerl.at/mcp
```

The browser should open and ask you to log in via OAuth.

## Legacy Header Setup

Older Gurkerl docs also show an `mcp-remote` setup that passes account
credentials as headers:

```json
{
  "mcpServers": {
    "gurkerl": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://mcp.gurkerl.at/mcp/",
        "--header",
        "rhl-email: ${RHL_EMAIL}",
        "--header",
        "rhl-pass: ${RHL_PASS}"
      ],
      "env": {
        "RHL_EMAIL": "email@gmail.com",
        "RHL_PASS": "your-password"
      }
    }
  }
}
```

## Recommended Architecture

Use two MCP layers:

1. Gurkerl official MCP
   - product search
   - promotions and discounts
   - cart/account operations

2. Local recommender MCP
   - your nutrition profile
   - scoring and ranking
   - Save Food prioritization
   - notification filtering

This keeps credentials and store-specific behavior in the official Gurkerl MCP,
while our code stays focused on recommendation quality.

## Local Discovery

Prefer testing the OAuth flow in a real MCP host first:

```bash
claude mcp add --transport http gurkerl-mcp https://mcp.gurkerl.at/mcp
```

Then run:

```text
/mcp
```

and authenticate `gurkerl-mcp` in the browser.

The local scripts in this repository are only inspectors/debug helpers. They are
not the recommended production connection path.

Legacy header-based inspection:

```bash
RHL_EMAIL=
python3 -m gurkerl_recommender.gurkerl_mcp_cli list-tools
```

That command uses direct HTTP MCP by default and asks the official Gurkerl MCP
which tools it exposes. To test the `mcp-remote` bridge instead, pass
`--transport remote`.

If Python HTTP is blocked by Cloudflare browser-signature checks, try the Node
inspector:

```bash
node scripts/list_gurkerl_tools.mjs
```

If the handwritten inspector hangs on the SSE stream, use the official MCP SDK:

```bash
node scripts/list_gurkerl_tools_sdk.mjs
```

The closest match to Gurkerl's documented setup is the SDK stdio client plus
`mcp-remote`:

```bash
node scripts/list_gurkerl_tools_remote_sdk.mjs
```

## Security Notes

- Do not commit credentials.
- Prefer environment variables on the VPS.
- Keep checkout or payment confirmation manual at first.
- Use the monitor for recommendations/notifications before allowing cart edits.
