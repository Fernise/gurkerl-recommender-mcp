import json
import unittest

from gurkerl_recommender.gurkerl_http_mcp_client import _parse_response


class GurkerlHttpMcpClientTest(unittest.TestCase):
    def test_parse_json_response(self) -> None:
        response = _parse_response(json.dumps({"jsonrpc": "2.0", "result": {}}))

        self.assertEqual(response, {"jsonrpc": "2.0", "result": {}})

    def test_parse_sse_response(self) -> None:
        response = _parse_response('event: message\ndata: {"result": {"tools": []}}\n\n')

        self.assertEqual(response, {"result": {"tools": []}})


if __name__ == "__main__":
    unittest.main()
