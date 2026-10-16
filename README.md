# Truthrail LLM MCP adapter

Dedicated **Streamable HTTP MCP** layer in front of the already verified Truthrail CLIProxyAPI on Render, separate from the infrastructure MCP gateway.

## State

`/health` reports HTTP 200 with `inference: disabled` initially. `/mcp` always requires a private bearer token; without a secret injected as `MCP_AUTH_BEARER` it responds HTTP 401. **No model is accessible on first deploy.**

This v0 contains exactly two MCP tools:

- `get_adapter_status`: bounded status with no secret material.
- `review_public_python`: one owner-consented public Python correctness review via fixed `opencode-go/glm-5.3-flash`, at most 2400 source bytes, 70 lines, 320 completion tokens and 1600 prompt tokens. No tool calls or retries.

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

## Authorization and cost model

Two independent gates: MCP caller authentication and gateway client authentication. Tool itself enforces public Python-only input, explicit broker-sharing consent, fixed model, fixed URL, no private source and no tools. One in-flight request and a process-local limit of eight calls per 24h mitigate accidental spending but **reset on restart**, so they are **not a hard budget**. Until an authenticated client, owner-approved limited task and suitable metering/spending guardrail are verified, keep `ENABLE_REVIEW=false` on public hosting.

## Testing

`python -m unittest discover -s tests -v` with packages pinned in `requirements.txt`. CI additionally builds a real image and verifies anonymous MCP POST yields 401; no provider call is made.

## Relationship to Truthrail

Truthrail remains the capability policy and GitHub source of truth; this service is only an implementation adapter. The original `render-python-code-review` GitHub Actions worker remains functional and is not replaced or broadened automatically.
