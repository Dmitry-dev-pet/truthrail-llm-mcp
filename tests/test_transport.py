"""Integration tests run once official MCP SDK dependencies are installed."""
import os
import unittest
from unittest import mock
from starlette.testclient import TestClient

from llm_mcp import server


class SecureTransportTests(unittest.TestCase):
    def test_not_provisioned_or_enabled(self):
        self.assertFalse(server.operational())
        self.assertFalse(server.AUTH_VALID)
        self.assertFalse(server.GATEWAY_VALID)

    def test_public_health_but_no_mcp_discovery_without_bearer(self):
        with TestClient(server.app, base_url='http://localhost:10000') as client:
            resp=client.get('/health')
            self.assertEqual(resp.status_code,200)
            self.assertEqual(resp.json()['inference'],'disabled')
            for url in ['/mcp','/mcp/','/random-path']:
                with self.subTest(url=url):
                    resp=client.post(url,json={'jsonrpc':'2.0','id':1,'method':'tools/list'})
                    self.assertEqual(resp.status_code,401)
                    self.assertNotIn('glm',resp.text)

    def test_bearer_does_not_grant_paid_inference_when_missing_upstream(self):
        # Does not mutate secrets in Render; test an isolated synthetic bearer.
        with mock.patch.object(server,'AUTH_VALID',True),mock.patch.object(server,'_AUTH_TOKEN','A'*43+'='):
            with TestClient(server.app,base_url='http://localhost:10000') as client:
                resp=client.post('/mcp',headers={'Authorization':'Bearer '+'A'*43+'=',
                         'MCP-Protocol-Version':'2026-07-28','Accept':'application/json'},
                         json={'jsonrpc':'2.0','id':1,'method':'tools/list'})
                self.assertNotEqual(resp.status_code,401)
                self.assertIn(resp.status_code,(200,202,400))
            self.assertFalse(server.operational())

if __name__=='__main__':unittest.main()
