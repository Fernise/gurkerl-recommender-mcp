from __future__ import annotations

import argparse
import json
from pathlib import Path

from gurkerl_recommender.env import load_dotenv
from gurkerl_recommender.gurkerl_http_mcp_client import GurkerlHttpMcpClient
from gurkerl_recommender.gurkerl_mcp_client import GurkerlMcpClient


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Inspect Gurkerl's official MCP.")
    parser.add_argument(
        "--transport",
        choices=("http", "remote"),
        default="http",
        help="Use direct HTTP MCP or the mcp-remote stdio bridge.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list-tools")

    call_tool = subparsers.add_parser("call-tool")
    call_tool.add_argument("name")
    call_tool.add_argument("--arguments", default="{}")

    args = parser.parse_args()
    client = GurkerlHttpMcpClient() if args.transport == "http" else GurkerlMcpClient()

    try:
        if args.command == "list-tools":
            result = client.list_tools()
        else:
            result = client.call_tool(args.name, json.loads(args.arguments))
    except RuntimeError as error:
        raise SystemExit(str(error)) from error

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
