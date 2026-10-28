import unittest
from unittest.mock import patch

from gurkerl_recommender.gurkerl_mcp_client import (
    GurkerlMcpClient,
    _encode_message,
    _read_response,
)


class GurkerlMcpClientTest(unittest.TestCase):
    def test_requires_credentials(self) -> None:
        client = GurkerlMcpClient()

        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "RHL_EMAIL, RHL_PASS"):
                client.list_tools()

    def test_command_uses_resolved_credentials(self) -> None:
        client = GurkerlMcpClient()

        with patch.dict(
            "os.environ",
            {"RHL_EMAIL": "person@example.com", "RHL_PASS": "secret"},
            clear=True,
        ):
            command = client._command()

        self.assertIn("--yes", command)
        self.assertIn("rhl-email: person@example.com", command)
        self.assertIn("rhl-pass: secret", command)

    def test_reads_framed_response(self) -> None:
        output = _encode_message({"jsonrpc": "2.0", "id": 2, "result": {"tools": []}})

        response = _read_response(output, request_id=2)

        self.assertEqual(response, {"jsonrpc": "2.0", "id": 2, "result": {"tools": []}})


if __name__ == "__main__":
    unittest.main()
