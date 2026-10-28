from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GurkerlMcpConfig:
    url: str = "https://mcp.gurkerl.at/mcp/"
    email_env: str = "RHL_EMAIL"
    password_env: str = "RHL_PASS"
    command: str = "npx"
    package: str = "mcp-remote"
    timeout_seconds: int = 30


class GurkerlMcpClient:
    """Small JSON-RPC client for Gurkerl's remote MCP via mcp-remote."""

    def __init__(self, config: GurkerlMcpConfig | None = None) -> None:
        self.config = config or GurkerlMcpConfig()

    def list_tools(self) -> dict[str, Any]:
        return self._single_request("tools/list", {})

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._single_request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )

    def _single_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._validate_credentials()
        initialize = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "gurkerl-recommender", "version": "0.1.0"},
            },
        }
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": method,
            "params": params,
        }

        stdin = "".join(
            [
                _encode_message(initialize),
                _encode_message(initialized),
                _encode_message(request),
            ]
        )
        process = subprocess.Popen(
            self._command(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy(),
        )
        try:
            stdout, stderr = process.communicate(
                input=stdin,
                timeout=self.config.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

        response = _read_response(stdout, request_id=2)
        if process.returncode not in (0, None) and response is None:
            detail = stderr.strip() or stdout.strip()
            raise RuntimeError(detail or "mcp-remote exited without a response")
        if response is None:
            detail = stderr.strip() or stdout.strip()
            raise RuntimeError(detail or "No matching MCP response received")
        if "error" in response:
            raise RuntimeError(json.dumps(response["error"], ensure_ascii=False))
        return response["result"]

    def _command(self) -> list[str]:
        email = os.environ[self.config.email_env]
        password = os.environ[self.config.password_env]
        return [
            self.config.command,
            "--yes",
            self.config.package,
            self.config.url,
            "--header",
            f"rhl-email: {email}",
            "--header",
            f"rhl-pass: {password}",
        ]

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


def _encode_message(payload: dict[str, Any]) -> str:
    body = json.dumps(payload)
    return f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}"


def _read_response(output: str, request_id: int) -> dict[str, Any] | None:
    framed = _read_framed_response(output, request_id)
    if framed is not None:
        return framed

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("id") == request_id:
            return payload
    return None


def _read_framed_response(output: str, request_id: int) -> dict[str, Any] | None:
    index = 0
    while index < len(output):
        header_end = output.find("\r\n\r\n", index)
        separator_length = 4
        if header_end == -1:
            header_end = output.find("\n\n", index)
            separator_length = 2
        if header_end == -1:
            return None

        headers = output[index:header_end].splitlines()
        content_length = None
        for header in headers:
            key, _, value = header.partition(":")
            if key.lower() == "content-length":
                content_length = int(value.strip())
                break
        if content_length is None:
            index = header_end + separator_length
            continue

        body_start = header_end + separator_length
        body = output[body_start : body_start + content_length]
        index = body_start + content_length
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            continue
        if payload.get("id") == request_id:
            return payload
    return None
