from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GurkerlHttpMcpConfig:
    url: str = "https://mcp.gurkerl.at/mcp/"
    email_env: str = "RHL_EMAIL"
    password_env: str = "RHL_PASS"
    timeout_seconds: int = 30


class GurkerlHttpMcpClient:
    """Direct Streamable HTTP MCP client for Gurkerl's official MCP."""

    def __init__(self, config: GurkerlHttpMcpConfig | None = None) -> None:
        self.config = config or GurkerlHttpMcpConfig()
        self.session_id: str | None = None
        self._next_id = 1

    def list_tools(self) -> dict[str, Any]:
        self.initialize()
        return self._request("tools/list", {})

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.initialize()
        return self._request("tools/call", {"name": name, "arguments": arguments})

    def initialize(self) -> dict[str, Any]:
        if self.session_id is not None:
            return {}
        result, headers = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "gurkerl-recommender",
                        "version": "0.1.0",
                    },
                },
            }
        )
        self.session_id = headers.get("mcp-session-id")
        self._post(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }
        )
        return result

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        response, _headers = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._id(),
                "method": method,
                "params": params,
            }
        )
        if "error" in response:
            raise RuntimeError(json.dumps(response["error"], ensure_ascii=False))
        return response["result"]

    def _post(self, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
        self._validate_credentials()
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.config.url,
            data=body,
            method="POST",
            headers=self._headers(),
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                response_body = response.read().decode("utf-8")
                return _parse_response(response_body), {
                    key.lower(): value for key, value in response.headers.items()
                }
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"Network error: {error.reason}") from error

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "rhl-email": os.environ[self.config.email_env],
            "rhl-pass": os.environ[self.config.password_env],
        }
        if self.session_id is not None:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    def _id(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value

    def _validate_credentials(self) -> None:
        missing = [
            name
            for name in (self.config.email_env, self.config.password_env)
            if not os.environ.get(name)
        ]
        if missing:
            raise RuntimeError(
                "Missing Gurkerl MCP credential environment variables: "
                + ", ".join(missing)
            )


def _parse_response(body: str) -> dict[str, Any]:
    stripped = body.strip()
    if not stripped:
        return {}
    data_lines = [
        line.removeprefix("data:").strip()
        for line in stripped.splitlines()
        if line.startswith("data:")
    ]
    if data_lines:
        stripped = "\n".join(data_lines)
    return json.loads(stripped)
