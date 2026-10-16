"""Blueprint can reference only an EXISTING gateway client key; never its upstream API key."""
import unittest
from pathlib import Path
from unittest import mock

import yaml

from llm_mcp import server

ROOT = Path(__file__).resolve().parents[1]


class RenderNativeLinkTests(unittest.TestCase):
    def test_blueprint_adopts_only_preexisting_mcp_service(self):
        blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
        self.assertEqual(set(blueprint), {"services"})
        self.assertEqual(len(blueprint["services"]), 1)
        svc = blueprint["services"][0]
        self.assertEqual(svc["name"], "truthrail-llm-mcp")
        self.assertEqual(svc["type"], "web")
        self.assertEqual(svc["runtime"], "docker")
        self.assertEqual(svc["plan"], "free")
        self.assertEqual(svc["region"], "frankfurt")
        self.assertEqual(svc["repo"], "https://github.com/Dmitry-dev-pet/truthrail-llm-mcp")
        self.assertEqual(svc["branch"], "main")
        self.assertEqual(svc["autoDeployTrigger"], "off")
        self.assertEqual(svc["healthCheckPath"], "/health")
        self.assertEqual(svc["previews"]["generation"], "off")

    def test_render_references_client_secret_not_provider_key(self):
        svc = yaml.safe_load((ROOT / "render.yaml").read_text())["services"][0]
        env = svc["envVars"]
        keys = [item["key"] for item in env]
        self.assertEqual(set(keys), {
            "PORT", "ENABLE_REVIEW", "MCP_AUTH_BEARER", "GATEWAY_CLIENT_KEY"
        })
        self.assertEqual(len(keys), len(set(keys)))
        mapping = {item["key"]: item for item in env}
        self.assertEqual(mapping["ENABLE_REVIEW"]["value"], "false")
        self.assertEqual(mapping["PORT"]["value"], "10000")
        self.assertEqual(mapping["MCP_AUTH_BEARER"],
                         {"key": "MCP_AUTH_BEARER", "generateValue": True})
        self.assertEqual(
            mapping["GATEWAY_CLIENT_KEY"],
            {
                "key": "GATEWAY_CLIENT_KEY",
                "fromService": {
                    "type": "web",
                    "name": "truthrail-llm-gateway",
                    "envVarKey": "CPA_CLIENT_API_KEY",
                },
            },
        )
        self.assertNotIn("CPA_OPENCODE_GO_API_KEY", str(env))
        self.assertNotIn("OPENCODE_GO_API_KEY", str(env))
        self.assertNotIn("render-cliproxy", str(env))

    def test_status_without_probe_does_not_call_any_gateway(self):
        with mock.patch.object(server.httpx, "Client") as http_client:
            answer = server.get_adapter_status()
        self.assertEqual(answer["gateway_auth_probe"], "not_requested")
        self.assertFalse(answer["model_inference_called_by_probe"])
        http_client.assert_not_called()

    def test_probe_gets_exact_gateway_model_catalog_without_inference(self):
        calls = []
        class FakeResponse:
            status_code = 200
            content = b'{"data":[{"id":"opencode-go/glm-5.3-flash"}]}'
        class FakeClient:
            def __init__(self, *, timeout, follow_redirects, trust_env):
                self.assert_isolated = not follow_redirects and not trust_env
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def get(self, url, headers):
                calls.append((url, headers))
                return FakeResponse()
        synthetic = "8" * 64
        with mock.patch.object(server, "GATEWAY_VALID", True), \
             mock.patch.object(server, "_GATEWAY_KEY", synthetic), \
             mock.patch.object(server.httpx, "Client", FakeClient):
            status = server.get_adapter_status(verify_gateway=True)
        self.assertEqual(status["gateway_auth_probe"], "gateway_client_authenticated")
        self.assertFalse(status["model_inference_called_by_probe"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0],
                         "https://truthrail-llm-gateway.onrender.com/v1/models")
        self.assertEqual(calls[0][1]["Authorization"], "Bearer " + synthetic)
        self.assertNotIn(synthetic, str(status))
        self.assertNotIn("provider_key", str(status))

    def test_bad_gateway_credential_is_not_exposed(self):
        class FakeResp:
            status_code = 401
            content = b"denied"
        class FakeClient:
            def __init__(self, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def get(self, url, headers): return FakeResp()
        with mock.patch.object(server, "GATEWAY_VALID", True), \
             mock.patch.object(server, "_GATEWAY_KEY", "9"*64), \
             mock.patch.object(server.httpx, "Client", FakeClient):
            self.assertEqual(server._probe_existing_gateway(), "gateway_client_denied")

    def test_missing_link_is_not_used_for_inference(self):
        with mock.patch.object(server, "GATEWAY_VALID", False):
            self.assertEqual(
                server.get_adapter_status(verify_gateway=True)["gateway_auth_probe"],
                "client_credential_not_provisioned"
            )
            self.assertFalse(server.operational())


if __name__ == "__main__":
    unittest.main()
