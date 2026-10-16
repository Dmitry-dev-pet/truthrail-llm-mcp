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

## Completed: one-time CLI/GitHub Actions key link

The owner completed the one-time key linkage **without a Blueprint sync**.
A reviewed private GitHub Actions workflow computed both strongly separated
machine-client credentials from the original private OpenCode Go sandbox key
and used Render's per-variable REST API to update only the existing MCP
service `srv-db8nofcs728c73adae10`. The upstream provider key was NEVER
copied into this MCP service.

Verification receipts:

- [it-mentor PR #87](https://github.com/Dmitry-dev-pet/it-mentor/pull/87)
- [Owner Issue #88](https://github.com/Dmitry-dev-pet/it-mentor/issues/88)
- [Completed run #38844708536](https://github.com/Dmitry-dev-pet/it-mentor/actions/runs/38844708536)
- Existing MCP deploy: `dep-db8pebmq1p3s738u3i50`, live, source
  `283dde69262e29eaa05798f75c1103bed6ed4101`

The workflow confirmed authorized MCP `get_adapter_status(verify_gateway=true)`
successfully contacted the existing CLIProxyAPI `/v1/models` endpoint. It
also confirmed anonymous MCP access was rejected and `/health` reported
`inference: disabled`. No LLM calls were made.

The source `render.yaml` reference remains an **optional** approach; it
was not synced. There is no reason to adopt a Blueprint merely to complete
this already working machine-key link. A future Blueprint sync must not
duplicate the MCP service or overwrite the newly provisioned credentials.

Before considering paid model invocation, establish an approved client
credential handoff and enforce durable quotas. The temporary Render account
API key used by the one-time owner workflow must be revoked and its GitHub
`sandbox` copy deleted. Keep the original `OPENCODE_GO_API_KEY`.
## Still intentionally disabled

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
