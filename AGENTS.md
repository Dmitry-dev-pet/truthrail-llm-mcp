# Truthrail LLM MCP adapter contract

- This repository implements a separate LLM MCP transport. It is not the infra-access MCP and not a Truthrail agent.
- In default sealed mode all MCP routes return 401; `/health` exposes only generic status.
- Never store API keys, credentials, OAuth sessions or project private source in git, Docker build layers or logs.
- Do not add an arbitrary prompt, command, GitHub checkout, URL, model, provider, fallback, repository or OpenAI Responses proxy tool.
- `review_public_python` can run only after client authorization and separate protected gateway credential provisioning. It accepts public Python excerpts with explicit one-request approval; no tools.
- The reviewed Render Blueprint must manage **only** the existing
  `truthrail-llm-mcp` service; the existing `truthrail-llm-gateway`
  remains separate and is referenced only as a source of its
  `CPA_CLIENT_API_KEY` via `fromService`. Never reference the OpenCode Go
  upstream key or rotate the gateway's client key as a shortcut.
- `render.yaml` is source-only until deliberately synced in Render's UI.
  The synchronization must adopt the exact existing MCP service, not create
  a duplicate or silently deploy another model gateway.
- `get_adapter_status(verify_gateway=true)` may use exactly one bounded
  authorized GET to the fixed gateway's `/v1/models`, with no inference,
  no fallback and no response-body disclosure.
- A static private bearer is a valid machine-to-machine credential for
  clients that explicitly support it, but not equivalent to user-scoped OAuth.
  Do not require ChatGPT as an upstream/model or a mandatory MCP client.

- The temporary Render management API key is never consumed by the MCP server.
- This server is not an OAuth identity provider. ChatGPT plugin linking needs a reviewed OAuth identity provider, or an explicitly supported private plugin API-key connection; do not claim a bare 401 equals a complete OAuth flow.
- The original machine-client credential link has been independently verified
  through owner-only `it-mentor` Issue #88 / Actions #38844708536. The MCP
  server has only two protected client credentials, not the upstream OpenCode
  Go provider key. The working old gateway remains unchanged.
- The optional `render.yaml` is source-only and was not synced. The complete
  operator link required no Blueprint; do not create a duplicate MCP service.
- Model calls remain deliberately disabled by `ENABLE_REVIEW=false` by default.
  An owner-reviewed **single synthetic acceptance only** requires both
  `REVIEW_ACCEPTANCE_ONLY=true` and `REVIEW_ACCEPTANCE_EXPIRES` set to a
  future Unix timestamp within 30 minutes. It only permits the fixed
  public `synthetic/mcp-acceptance.py` even-number bug snippet, one model
  request per process, no tools or provider/model choice. The expiry is
  not durable billing control; reset `ENABLE_REVIEW=false` after the test.
  Never infer general inference authority from the temporary smoke.
- One process and best-effort local quota are not a financial budget guarantee. Do not activate unattended inference without durable metering and operator-defined cost ceiling.
- All changes: branch, CI, PR, merge. The gateway route and working GitHub issue worker are unchanged unless separately reviewed.
