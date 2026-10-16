# Existing Render-to-Render LLM credential link

This procedure **adopts the already-running** Render web service
`truthrail-llm-mcp` in the same Frankfurt workspace as
`truthrail-llm-gateway`. It does NOT deploy a new model provider, copy the
upstream OpenCode Go key, or replace the working GitHub review worker.

## Verified existing resources (16 October 2026)

- Source client service: `truthrail-llm-mcp`,
  Render ID `srv-db8nofcs728c73adae10`, repo `Dmitry-dev-pet/truthrail-llm-mcp`.
- Source of gateway client credential: `truthrail-llm-gateway`,
  Render ID `srv-db8m8dm7bikc73cq8n2g`.
- Both services: same Render workspace `tea-d4oahpi4i8rc73eus0tg`,
  Frankfurt, free, and auto-deploy disabled.
- The gateway holds `CPA_CLIENT_API_KEY` (client authorization) separately
  from `CPA_OPENCODE_GO_API_KEY` (upstream broker authorization).
- Earlier live verification of actual OpenCode Go coding inference:
  https://github.com/Dmitry-dev-pet/it-mentor/actions/runs/38831339510

## Why this is one safe connection, not another proxy

`render.yaml` declares only `truthrail-llm-mcp`, NOT
`truthrail-llm-gateway`. Its `GATEWAY_CLIENT_KEY` env var is linked to
the gateway's **existing CLIENT** authorization through the official Render
Blueprint reference:

```yaml
- key: GATEWAY_CLIENT_KEY
  fromService:
    type: web
    name: truthrail-llm-gateway
    envVarKey: CPA_CLIENT_API_KEY
```

Render reads the referenced environment variable *within the same workspace*
during a Blueprint sync and inserts it into the MCP service's protected
environment. No key is copied into GitHub, ChatGPT, a new token store or
a user-facing tool response. The *OpenCode Go provider secret is not referenced.*

## Operator-only sync of the existing service

The current connected Render API tooling can merge plaintext `key/value`
pairs but has **no Blueprint-sync or protected fromService setter**.
Therefore, do NOT pass a secret through that API or simulate the reference
with a literal `$VARIABLE` string.

1. In Render, open the existing `truthrail-llm-mcp` web service and verify
   its name, repository, free plan, Frankfurt region, Docker runtime and
   auto-deploy OFF.
2. Open **Blueprints** in the *same* Render workspace. Create a new Blueprint
   from this repo's root `render.yaml`, using the **existing** service.
   Render supports adopting existing resources into a Blueprint.
3. **Preview the plan before syncing.** It must update the existing
   `truthrail-llm-mcp` service ID `srv-db8nofcs728c73adae10`.
   STOP if Render proposes a new suffixed duplicate service, edits
   `truthrail-llm-gateway`, enables auto-deploy, changes plan, or replaces
   an existing secret with a literal/empty value.
4. Sync the Blueprint only after verifying the plan. It should:
   - Link `GATEWAY_CLIENT_KEY` to the gateway's `CPA_CLIENT_API_KEY`.
   - Generate a **distinct** `MCP_AUTH_BEARER` (256-bit) for private
     machine-to-machine clients.
   - Leave `ENABLE_REVIEW=false` and the model path disabled.
5. Check that the existing MCP service redeploys successfully and that
   `GET /health` still returns HTTP 200 with `inference: disabled`.
   Verify anonymous `POST /mcp` still responds 401.
6. An authenticated private MCP client can then call
   `get_adapter_status(verify_gateway=true)`. This makes a single
   **read-only GET /v1/models** to the existing gateway. It must return
   `gateway_auth_probe=gateway_client_authenticated` before proceeding.
   This call makes **zero LLM inference requests**, and returns no keys.

`fromService` values refresh on Blueprint sync, NOT whenever the source
environment variable changes. After rotating the gateway client key,
resync the MCP Blueprint before expecting the new key to work.

## Not part of the sync

- Do not set `ENABLE_REVIEW=true` yet. A real model call is a separate
  explicit owner authorization; the model remains disabled meanwhile.
- Do not grant this MCP source any GitHub, SSH, Docker, private repository,
  filesystem, infrastructure, model-switching or arbitrary URL rights.
- Do not configure a ChatGPT-specific login. Independent MCP clients can
  authenticate with their own permitted bearer token; ChatGPT plugin login
  would be a separate integration requiring its own supported mechanism.
- Do not treat the process-local quota as a durable financial cap.
- Do not reissue the temporary account-wide Render API key. Blueprint
  synchronization occurs through the owner's Render UI.

The original `Dmitry-dev-pet/it-mentor` public-Python code-review workflow
remains the only independently verified **live inference** caller until the
new MCP transport's own authenticated inference passes a separate acceptance.
