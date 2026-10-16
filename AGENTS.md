# Truthrail LLM MCP adapter contract

- This repository implements a separate LLM MCP transport. It is not the infra-access MCP and not a Truthrail agent.
- In default sealed mode all MCP routes return 401; `/health` exposes only generic status.
- Never store API keys, credentials, OAuth sessions or project private source in git, Docker build layers or logs.
- Do not add an arbitrary prompt, command, GitHub checkout, URL, model, provider, fallback, repository or OpenAI Responses proxy tool.
- `review_public_python` can run only after client authorization and separate protected gateway credential provisioning. It accepts public Python excerpts with explicit one-request approval; no tools.
- The temporary Render management API key is never consumed by the MCP server.
- This server is not an OAuth identity provider. ChatGPT plugin linking needs a reviewed OAuth identity provider, or an explicitly supported private plugin API-key connection; do not claim a bare 401 equals a complete OAuth flow.
- One process and best-effort local quota are not a financial budget guarantee. Do not activate unattended inference without durable metering and operator-defined cost ceiling.
- All changes: branch, CI, PR, merge. The gateway route and working GitHub issue worker are unchanged unless separately reviewed.
