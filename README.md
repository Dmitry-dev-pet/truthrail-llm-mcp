# Truthrail LLM MCP adapter

Dedicated **Streamable HTTP MCP** layer in front of the already verified Truthrail CLIProxyAPI on Render, separate from the infrastructure MCP gateway.

## State

`/health` reports HTTP 200 with `inference: disabled` initially. `/mcp` always requires a private bearer token; without a secret injected as `MCP_AUTH_BEARER` it responds HTTP 401. **No model is accessible on first deploy.**

This v0 contains exactly two MCP tools:

- `get_adapter_status`: bounded status with no secret material.
- `review_public_python`: one owner-consented public Python correctness review via fixed `opencode-go/glm-5.3-flash`, at most 2400 source bytes, 70 lines, 320 completion tokens and 1600 prompt tokens. No tool calls or retries.

The gateway model has already been verified through the separate owner-gated GitHub Action: [run #38831339510](https://github.com/Dmitry-dev-pet/it-mentor/actions/runs/38831339510). This **does not** prove the new MCP transport or ChatGPT OAuth is connected.

## Native connection to the existing Render gateway

This MCP server is **not a second model proxy**. It calls the existing
`truthrail-llm-gateway` → OpenCode Go path.

The reviewed `render.yaml` can link its `GATEWAY_CLIENT_KEY` directly to
the existing gateway's `CPA_CLIENT_API_KEY` using Render's same-workspace
`fromService` reference. The OpenCode Go provider key stays **only in the
gateway** and is never copied to the MCP or GitHub.

This Blueprint is NOT applied automatically to the already-created Render
service. Follow the safe existing-service adoption checklist in
[docs/RENDER_GATEWAY_LINK.md](docs/RENDER_GATEWAY_LINK.md). The first
Blueprint sync keeps `ENABLE_REVIEW=false`, so model calls remain disabled.

Once an independent MCP client has its private bearer, it can call
`get_adapter_status(verify_gateway=true)`: a read-only, no-token-spend
authentication check of the gateway's `/v1/models`. It does not send
a chat/completions request. A client does **not** have to be ChatGPT.

## Deployment

Public code-only repo, Docker, Frankfurt `free`, one Uvicorn worker, auto-deploy off. An optional `render.yaml` declares the same service and secrets for initial Blueprint setup. It is not automatically applied to a service created directly through the Render API.

Secret configuration (set privately in Render Environment only):

| Name | Purpose |
| --- | --- |
| `MCP_AUTH_BEARER` | New high-entropy private bearer for isolated operator acceptance. **Not** a user OAuth identity. |
| `GATEWAY_CLIENT_KEY` | Protected client key already accepted by the fixed CLIProxyAPI gateway. Do not reuse upstream provider key or copy from git. |
| `ENABLE_REVIEW` | Must literally be `true` *as a separate deployment decision* before model calls are allowed. Default `false`. |
| `PORT` | Render listening port, default `10000`. |

The server's initial deployment has no model or MCP client credentials. Render can now link its gateway client key without ever exporting a secret value (see the Blueprint instructions above). Machine-to-machine MCP clients can use an owner-provisioned bearer; ChatGPT-specific OAuth is not a requirement for this independent service, although it would need its own separate reviewed connector configuration if ever requested.

## Authorization and cost model

Two independent gates: MCP caller authentication and gateway client authentication. Tool itself enforces public Python-only input, explicit broker-sharing consent, fixed model, fixed URL, no private source and no tools. One in-flight request and a process-local limit of eight calls per 24h mitigate accidental spending but **reset on restart**, so they are **not a hard budget**. Until an authenticated client, owner-approved limited task and suitable metering/spending guardrail are verified, keep `ENABLE_REVIEW=false` on public hosting.

## Testing

`python -m unittest discover -s tests -v` with packages pinned in `requirements.txt`. CI additionally builds a real image and verifies anonymous MCP POST yields 401; no provider call is made.

## Relationship to Truthrail

Truthrail remains the capability policy and GitHub source of truth; this service is only an implementation adapter. The original `render-python-code-review` GitHub Actions worker remains functional and is not replaced or broadened automatically.
