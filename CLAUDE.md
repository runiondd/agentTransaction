# CLAUDE.md

## Project

AI agent-to-agent Solana token transfer POC. Two LangChain agents (Claude-powered) in separate Docker containers discover each other, exchange wallet addresses, and transfer SOL on devnet. React dashboard for visibility.

## Quick Reference

```bash
docker compose up -d          # Start everything
docker compose logs -f        # Watch all logs
docker compose down           # Stop everything
```

- Dashboard: http://localhost:3000
- Agent A API: http://localhost:8001
- Agent B API: http://localhost:8002
- Fund wallets: https://faucet.solana.com (get addresses from GET /status)

## Architecture

- `agent/` — Python FastAPI + LangChain agent (shared codebase, differentiated by env vars)
- `dashboard/` — React + Vite + Tailwind, served via nginx in Docker
- `docker-compose.yml` — 3 containers on a bridge network, agents use named volumes for wallet persistence

## Key Constraints

- **langchain must be <1.0.0** — v1.2 broke AgentExecutor imports. Pinned in requirements.txt.
- **Blockhash**: `get_latest_blockhash()` must be called without `commitment=Confirmed` or transactions fail with "Blockhash not found" on devnet.
- **LangChain agent output is a list**, not a string — any code parsing `result.get("output")` must handle both types.
- **Devnet airdrops are rate-limited** — if 429, manually fund via faucet.solana.com.
- **Vite env vars are build-time only** — changing VITE_AGENT_*_URL requires rebuilding the dashboard image.
- **Render PORT env var** — Dockerfile and config.py read PORT (Render) with fallback to AGENT_PORT (Docker Compose).

## Build & Test

```bash
docker compose build                              # Rebuild all
docker compose build agent-a agent-b              # Rebuild agents only
python3 agent/tests/test_e2e.py                   # Quick smoke tests (containers must be running)
python -m pytest agent/tests/test_e2e.py -v       # Full E2E with transfers
```

## Don't

- Don't upgrade langchain past 0.x — the agent code uses the 0.3 API
- Don't add `commitment=Confirmed` to `get_latest_blockhash` — causes stale blockhash errors
- Don't build SPL token support — intentionally skipped, doesn't add architectural proof value
- Don't deploy to cloud for live demo — too expensive for a POC, use screen recording instead
