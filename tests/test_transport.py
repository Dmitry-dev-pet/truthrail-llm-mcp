"""HTTP auth tests against one shared, startup-once MCP 2 session manager."""
import unittest
from unittest import mock
from starlette.testclient import TestClient

from llm_mcp import server


class SecureTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # MCP 2's session manager deliberately forbids entering lifespan twice.
        cls.client = TestClient(server.app, base_url="http://localhost:10000")
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_no_credentials_or_paid_model_by_default(self):
        self.assertFalse(server.operational())
        self.assertFalse(server.AUTH_VALID)
        self.assertFalse(server.GATEWAY_VALID)

    def test_public_health_and_no_anonymous_mcp_access(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["inference"], "disabled")
        for url in ("/mcp", "/mcp/", "/random-path"):
            with self.subTest(url=url):
                resp = self.client.post(
                    url,
                    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                )
                self.assertEqual(resp.status_code, 401)
                self.assertNotIn("glm-5.3", resp.text)

    def test_synthetic_bearer_never_enables_upstream_without_second_key(self):
        token = "A" * 43 + "="
        with mock.patch.object(server, "AUTH_VALID", True), mock.patch.object(
            server, "_AUTH_TOKEN", token
        ):
            resp = self.client.post(
                "/mcp",
                headers={
                    "Authorization": "Bearer " + token,
                    "MCP-Protocol-Version": "2026-07-28",
                    "Accept": "application/json",
                },
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            )
            self.assertNotEqual(resp.status_code, 401)
            self.assertIn(resp.status_code, (200, 202, 400))
            self.assertFalse(server.operational())

    def test_wrong_token_is_rejected(self):
        with mock.patch.object(server, "AUTH_VALID", True), mock.patch.object(
            server, "_AUTH_TOKEN", "B" * 43 + "="
        ):
            resp = self.client.post(
                "/mcp",
                headers={"Authorization": "Bearer " + "A" * 43 + "="},
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            )
        self.assertEqual(resp.status_code, 401)


if __name__ == "__main__":
    unittest.main()
