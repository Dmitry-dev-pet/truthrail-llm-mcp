"""Offline tests for expiring synthetic one-shot MCP acceptance."""
import json
import time
import unittest
from unittest import mock

from llm_mcp import server
from llm_mcp.policy import LocalReviewQuota

REVIEW = "This code returns True for odd values, not even. On line 2 use == 0; test both 2 and 3."


class AcceptanceGuardTests(unittest.TestCase):
    def test_environment_is_sealed_in_ci_and_production_by_default(self):
        self.assertFalse(server.operational())
        self.assertFalse(server.ACCEPTANCE_ONLY)
        self.assertFalse(server.REVIEW_ENABLED)
        self.assertEqual(server.QUOTA.max_calls, 1)

    def test_all_credentials_and_explicit_test_switch_required(self):
        expiry = str(int(time.time()) + 600)
        kwargs = {
            "REVIEW_ENABLED": True,
            "AUTH_VALID": True,
            "GATEWAY_VALID": True,
            "ACCEPTANCE_ONLY": True,
            "ACCEPTANCE_EXPIRES": expiry,
        }
        with mock.patch.multiple(server, **kwargs):
            self.assertTrue(server.operational())
            for attr in ("REVIEW_ENABLED", "AUTH_VALID",
                         "GATEWAY_VALID", "ACCEPTANCE_ONLY"):
                with mock.patch.object(server, attr, False):
                    self.assertFalse(server.operational(), attr)

    def test_expiry_is_enforced_and_far_future_denied(self):
        now = 1800000000
        common = {"REVIEW_ENABLED": True, "AUTH_VALID": True,
                  "GATEWAY_VALID": True, "ACCEPTANCE_ONLY": True}
        with mock.patch.multiple(server, **common):
            with mock.patch.object(server.time, "time", return_value=now):
                for expiry in ("", "zero", "0", str(now-1),
                               str(now), str(now+1900), "9"*100):
                    with self.subTest(expiry=expiry):
                        with mock.patch.object(server,"ACCEPTANCE_EXPIRES", expiry):
                            self.assertFalse(server.operational())
                with mock.patch.object(server, "ACCEPTANCE_EXPIRES", str(now+600)):
                    self.assertTrue(server.operational())
            with mock.patch.object(server.time, "time", return_value=now+600):
                with mock.patch.object(server, "ACCEPTANCE_EXPIRES", str(now+600)):
                    self.assertFalse(server.operational())

    def test_dynamic_python_snippets_never_reach_gateway(self):
        code = server.ACCEPTANCE_CODE.replace("== 1", "== 0")
        with mock.patch.object(server, "operational", return_value=True):
            with mock.patch.object(server.httpx, "Client") as client:
                answer = server.review_public_python(
                    code=code,
                    source_label=server.ACCEPTANCE_SOURCE,
                    classification="public",
                    share_with_opencode_go=True,
                )
            self.assertEqual(answer["status"], "blocked")
            self.assertEqual(answer["reason"], "only_reviewed_acceptance_fixture_allowed")
            client.assert_not_called()

    def test_fixture_source_and_consent_are_exact(self):
        with mock.patch.object(server, "operational", return_value=True):
            with mock.patch.object(server.httpx, "Client") as client:
                for kwargs in (
                    {"source_label": "another-file.py"},
                    {"classification": "private"},
                    {"share_with_opencode_go": False},
                ):
                    args = {
                        "code": server.ACCEPTANCE_CODE,
                        "source_label": server.ACCEPTANCE_SOURCE,
                        "classification": "public",
                        "share_with_opencode_go": True,
                    }
                    args.update(kwargs)
                    with self.subTest(kwargs=kwargs):
                        response = server.review_public_python(**args)
                        self.assertEqual(response["status"], "blocked")
                client.assert_not_called()

    def test_one_real_call_shape_through_fixed_gateway_only(self):
        calls=[]
        class FakeResponse:
            status_code=200
            content=b'{"synthetic":"yes"}'
            def json(self):
                return {
                    "model":"glm-5.3-flash",
                    "choices":[{"finish_reason":"stop",
                       "message":{"role":"assistant","content":REVIEW}}],
                    "usage":{"prompt_tokens":155,"completion_tokens":75},
                }
        class Client:
            def __init__(self, **kwargs):
                self.kwargs=kwargs
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def post(self,url,json,headers):
                calls.append((url,json,headers,self.kwargs))
                return FakeResponse()
        with mock.patch.object(server,"operational",return_value=True), \
             mock.patch.object(server,"QUOTA",LocalReviewQuota(max_calls=1)), \
             mock.patch.object(server,"_GATEWAY_KEY","synthetic-gateway-client-"+"X"*40), \
             mock.patch.object(server,"_AUTH_TOKEN","synthetic-mcp-auth-"+"Y"*40), \
             mock.patch.object(server.httpx,"Client",Client):
            answer=server.review_public_python(
                code=server.ACCEPTANCE_CODE,
                source_label=server.ACCEPTANCE_SOURCE,
                classification="public",
                share_with_opencode_go=True,
            )
            self.assertEqual(answer["status"],"executed_needs_owner_review")
            self.assertEqual(answer["input_tokens"],155)
            self.assertEqual(answer["output_tokens"],75)
            self.assertEqual(answer["model"],"opencode-go/glm-5.3-flash")
            self.assertNotIn("synthetic-mcp-auth-",str(answer))
            second=server.review_public_python(
                code=server.ACCEPTANCE_CODE,
                source_label=server.ACCEPTANCE_SOURCE,
                classification="public",
                share_with_opencode_go=True,
            )
            self.assertEqual(second["status"],"blocked")
            self.assertEqual(second["reason"],"concurrency_or_local_quota_exceeded")
        self.assertEqual(len(calls),1)
        url,payload,headers,options=calls[0]
        self.assertEqual(url,"https://truthrail-llm-gateway.onrender.com/v1/chat/completions")
        self.assertEqual(payload["model"],"opencode-go/glm-5.3-flash")
        self.assertEqual(payload["max_tokens"],320)
        self.assertFalse(payload["stream"])
        self.assertNotIn("tools",payload)
        self.assertTrue(headers["Authorization"].startswith("Bearer synthetic-gateway-"))
        self.assertFalse(options["trust_env"])
        self.assertFalse(options["follow_redirects"])

    def test_status_reports_no_general_inference(self):
        status=server.get_adapter_status(verify_gateway=False)
        self.assertFalse(status["general_inference_enabled"])
        self.assertTrue(status["test_only_automatic_expiry"])
        self.assertEqual(status["state"],"sealed_no_model_access")


if __name__ == "__main__":
    unittest.main()
