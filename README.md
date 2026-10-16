# Truthrail LLM MCP adapter

Dedicated **Streamable HTTP MCP** layer in front of the already verified Truthrail CLIProxyAPI on Render, separate from the infrastructure MCP gateway.

## State

`/health` reports HTTP 200 with `inference: disabled` initially. `/mcp` always requires a private bearer token; without a secret injected as `MCP_AUTH_BEARER` it responds HTTP 401. **No model is accessible on first deploy.**

This v0 contains exactly two MCP tools:

- `get_adapter_status`: bounded status with no secret material.
- `review_public_python`: currently only a **fixed public synthetic Python acceptance snippet**, not general code review. The response is limited to 320 completion tokens and 1600 prompt tokens, with no model tools or retries. It cannot run without a separate temporary owner-enabled acceptance window.

The gateway model has already been verified through the separate owner-gated GitHub Action: [run #38831339510](https://github.com/Dmitry-dev-pet/it-mentor/actions/runs/38831339510). This **does not** prove the new MCP transport or ChatGPT OAuth is connected.

## Connected to existing Render CLIProxyAPI (verified)

An owner-only, one-time GitHub workflow completed the protected machine-client
link on 16 October 2026. No Blueprint synchronization was necessary.
The existing Render MCP service was updated and redeployed **in place**.

- Source owner workflow: [it-mentor PR #87](https://github.com/Dmitry-dev-pet/it-mentor/pull/87)
- Owner trigger: [Issue #88](https://github.com/Dmitry-dev-pet/it-mentor/issues/88)
- Verified authenticated MCP-to-gateway read-only call:
  [Actions #38844708536](https://github.com/Dmitry-dev-pet/it-mentor/actions/runs/38844708536)
- Current live deployment: `dep-db8pebmq1p3s738u3i50` on
  existing `srv-db8nofcs728c73adae10`.

The original `CPA_OPENCODE_GO_API_KEY` remains **only** in the existing
CLIProxyAPI and its owning protected sandbox. The MCP environment now holds
separate derived `GATEWAY_CLIENT_KEY` and `MCP_AUTH_BEARER` machine credentials.
The model tool still returns `blocked`: `ENABLE_REVIEW=false`.
Existing GitHub-based Python code review remains operational.

**No need to visit Blueprints or copy keys manually.** The `render.yaml`
`fromService` definition is only an optional source-controlled alternative
that was not applied. Do not adopt it now unless separately reviewing
the plan and ensuring it changes only the same existing MCP service.

An authorized client can call `get_adapter_status(verify_gateway=true)`
to check the existing CLIProxyAPI's `/v1/models` endpoint without paying
for model inference. This succeeded in the owner workflow. Client credential
distribution to independent tools and enabling model calls require
separate reviewed authority and durable budget controls.
## Deployment

Public code-only repo, Docker, Frankfurt `free`, one Uvicorn worker, auto-deploy off. An optional `render.yaml` declares the same service and secrets for initial Blueprint setup. It is not automatically applied to a service created directly through the Render API.

Secret configuration (set privately in Render Environment only):

| Name | Purpose |
| --- | --- |
| `MCP_AUTH_BEARER` | New high-entropy private bearer for isolated operator acceptance. **Not** a user OAuth identity. |
| `GATEWAY_CLIENT_KEY` | Protected client key already accepted by the fixed CLIProxyAPI gateway. Do not reuse upstream provider key or copy from git. |
| `ENABLE_REVIEW` | Must literally be `true` *as a separate deployment decision* before model calls are allowed. Default `false`. |
| `PORT` | Render listening port, default `10000`. |

The server's **initial** deployment was intentionally sealed without client credentials. The owner-provisioned one-time GitHub route has now installed both protected machine-client credentials on the existing Render service; the upstream provider key remains absent here. `ENABLE_REVIEW=false` remains the independent model-inference gate. ChatGPT OAuth is not a requirement for this independent service.

## One-shot live coding acceptance (temporary, no general access)

Before enabling regular tool calls, the service supports only a **time-limited
synthetic acceptance smoke**. The following THREE runtime settings must be
explicitly set through the owner's protected Render service settings,
**in addition** to the two existing client credentials:

- `ENABLE_REVIEW=true`
- `REVIEW_ACCEPTANCE_ONLY=true`
- `REVIEW_ACCEPTANCE_EXPIRES=<future Unix epoch in seconds>`, at most **1800**
  seconds ahead of the current clock.

Even then, the tool accepts only this exact pair:

- Source: `synthetic/mcp-acceptance.py`
- Public code: `def is_even(number: int) -> bool:\n    return number % 2 == 1\n`

The caller must also set `classification=public` and
`share_with_opencode_go=true` for this particular request. All other
snippets are blocked. The in-memory meter permits **one attempt per
process**; expiry prevents further use without an authorized new rollout.
**Neither is a durable monetary quota.** The original client bearer is held
only in the owning private sandbox, not embedded in ChatGPT or source.

An owner-authorized single GitHub Issue smoke may call this existing MCP
through its protected bearer and confirm a genuine OpenCode Go coding review.
Once complete, reset `ENABLE_REVIEW=false`,
`REVIEW_ACCEPTANCE_ONLY=false`, and `REVIEW_ACCEPTANCE_EXPIRES=0`
through Render settings and verify the redeploy. A failed smoke still
requires closing these settings. This temporary path does NOT authorize
continuous OpenCode Go inference. Durable quotas and independently
approved client identity are required for regular use.

## Authorization and cost model

Two independent gates: MCP caller authentication and gateway client authentication. The currently reviewed third gate is a **fixed synthetic test plus a short expiry**. The tool rejects arbitrary snippets, private source, URLs, model switching and model tools. The in-memory one-attempt meter resets on restart, so it is **not a hard monetary budget**. After a single, owner-authorized acceptance test, reset `ENABLE_REVIEW=false` and keep general model access disabled until a durable quota and client authorization are reviewed.

## Testing

`python -m unittest discover -s tests -v` with packages pinned in `requirements.txt`. CI additionally builds a real image and verifies anonymous MCP POST yields 401; no provider call is made.

## Relationship to Truthrail

Truthrail remains the capability policy and GitHub source of truth; this service is only an implementation adapter. The original `render-python-code-review` GitHub Actions worker remains functional and is not replaced or broadened automatically.
