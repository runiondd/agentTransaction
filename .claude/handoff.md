# Context Handoff

> Generated: 2026-03-13T19:55:00Z
> Session: First E2E validation and bug fixing of agent-to-agent Solana transfer POC
> Phase: Milestone 6 complete (E2E validated), Milestone 7 next (observability & polish)

## Status Summary

The core POC is fully functional and validated end-to-end. Two LangChain agents (Claude-powered) in separate Docker containers successfully discover each other, exchange wallet addresses via HTTP, transfer SOL on Solana devnet, and confirm receipt — all orchestrated autonomously by the AI agent. The React dashboard serves correctly. Three bugs were found and fixed during validation. Remaining work is tests, polish, and the stretch SPL token feature.

## Completed This Session

- [x] Verified all 3 Docker containers build and start (`docker compose up` works)
- [x] Verified wallet keypair generation and persistence across restarts (Docker volumes)
- [x] Verified `/status`, `/transactions`, `/message` endpoints all functional
- [x] Verified inter-agent communication over Docker network (agent-a can reach agent-b:8000)
- [x] Fixed LangChain version incompatibility — pinned `langchain<1.0.0` in requirements.txt (v1.2 removed `AgentExecutor` from `langchain.agents`)
- [x] Fixed stale blockhash error — removed `commitment=Confirmed` from `get_latest_blockhash()` in `agent/wallet/transfer.py`
- [x] Fixed transaction logging crash — agent output is a list not a string; added type coercion in `agent/agent/agent.py` line 59
- [x] Completed 2 successful end-to-end transfers (A→B 0.5 SOL, A→B 0.25 SOL) with full LangChain agent flow
- [x] Verified balances update correctly (Agent A: 4.25 SOL, Agent B: 5.75 SOL)
- [x] Verified both sender and receiver transaction logs work
- [x] Created initial git commit (eb43b23) with all project files

## In Progress (Partially Done)

- [ ] Dashboard browser testing
  - **State:** Dashboard serves at localhost:3000 (confirmed via curl), but has NOT been tested in an actual browser. CORS issues likely exist when the browser tries to reach agents at localhost:8001/8002.
  - **Files touched:** None yet
  - **Next action:** Open http://localhost:3000 in a browser, check console for CORS errors. If present, verify CORS config in `agent/main.py` allows the dashboard origin.

## Queued (Not Yet Started)

- [ ] Task 6.4: E2E smoke test script (`agent/tests/test_e2e.py`) — automated version of what we did manually
- [ ] Task 7.1: Structured logging — consistent JSON format, agent_id prefix on all log lines
- [ ] Task 7.2: Error handling hardening — insufficient balance, peer down, RPC timeouts surfaced to dashboard
- [ ] Task 7.3: README with setup docs (currently exists but needs real content)
- [ ] Milestone 8 (stretch): SPL token support — minting, transfers, dashboard display
- [ ] Minor: Agent A logs `counterparty: "agent-b"` (agent name) while Agent B logs actual wallet address — should be consistent

## Key Decisions Made

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Pin langchain<1.0.0 | v1.2 has completely different API (AgentExecutor moved/removed). Code was written for 0.3.x | Update code to v1.2 API — more work, not worth it for POC |
| Remove Confirmed commitment from get_latest_blockhash | Devnet with Confirmed commitment returns blockhashes that expire before tx submission | Use Finalized (even more conservative), or add preflight skip |
| Coerce agent output to string for tx logging | LangChain returns list of content blocks, not a plain string | Restructure to parse structured output — overkill for logging |

## Problems Encountered

| Problem | Resolution | Notes |
|---------|------------|-------|
| Devnet airdrop rate limited (429) | User manually funded wallets via faucet.solana.com | Both wallets funded with 5 SOL each. Addresses: Agent A: `9UJr4iUGvdrPx3QVUXfnogbq9KU8Ar335P5MvXtvHoFC`, Agent B: `3EFejR59zULqbfDE3ZZMzvyryp6nw4bXvW9DgncUtzZK` |
| LangChain AgentExecutor import fails | Pinned langchain<1.0.0 in requirements.txt | The `except ImportError` fallback in routes.py masked this — it silently fell back to direct transfer |
| Blockhash not found on all 3 retry attempts | Removed commitment=Confirmed from get_latest_blockhash() | Retries were getting the same stale blockhash each time because the commitment level filtered out recent ones |
| Agent output parsing crash (`'list' object has no attribute 'lower'`) | Added type coercion in agent.py | This meant sender-side transaction logging silently failed |
| `masterplaybook/` is an embedded git repo | Excluded from git add, left as untracked | May need to be added as submodule or have its .git removed |

## Important Context

- **Wallet keypairs persist** in Docker named volumes (`agent-a-data`, `agent-b-data`). The same addresses will appear on restart.
- **Current balances:** Agent A ~4.25 SOL, Agent B ~5.75 SOL (after 2 test transfers). These reset if volumes are removed.
- **The `.env` file exists** but is gitignored. It contains `ANTHROPIC_API_KEY`. The glob tool doesn't find dotfiles easily — use `docker exec agent-a printenv ANTHROPIC_API_KEY` to verify.
- **Containers are currently running.** `docker compose down` to stop, `docker compose up -d` to restart.
- **The LangChain agent model** is set to `claude-sonnet-4-20250514` in `agent/agent/agent.py`.
- **Transfer takes ~20 seconds** end-to-end (4 LLM calls + Solana RPC + inter-agent HTTP).
- **The direct transfer fallback** in `routes.py:_direct_transfer()` still works and bypasses the LangChain agent. It was the path used before we fixed the import.

## Files Modified This Session

```
agent/requirements.txt          — pinned langchain<1.0.0
agent/wallet/transfer.py        — removed Confirmed commitment from get_latest_blockhash
agent/agent/agent.py            — fixed list-to-string coercion for agent output
```

## Resume Instructions

1. Read this file and `tasks.md` for full task breakdown
2. **Test the dashboard in a browser** — open http://localhost:3000 (containers should still be running). Check browser console for CORS errors. If agents are down, run `docker compose up -d`.
3. If CORS issues exist, fix in `agent/main.py` (CORS middleware config)
4. Write the E2E smoke test (`agent/tests/test_e2e.py`) — automate what was done manually: start containers, check status, trigger transfer, verify balances
5. Then tackle Milestone 7 tasks (structured logging, error handling, README) per `tasks.md`

> **To resume:** Start by reading this file, then check if containers are running (`docker compose ps`). Test the dashboard in a browser. The user should not need to re-explain anything captured above.
