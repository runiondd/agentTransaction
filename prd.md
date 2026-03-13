# AI Agent-to-Agent Solana Token Transfer — Product Requirements Document

## 1. Overview

A proof-of-concept demonstrating that two fully independent AI agents — running in separate Docker containers with no shared state — can discover each other, exchange wallet addresses, and execute token transfers on the Solana blockchain. A web dashboard running in a third container provides real-time visibility into wallet balances and lets a user trigger agent-driven transfers with a click. The system uses LangChain/LangGraph for agent orchestration, agent-to-agent HTTP messaging for coordination, and Solana devnet for safe experimentation. This POC validates that autonomous AI agents can transact as independent peers on an open network.

## 2. Problem Statement

There's growing interest in autonomous AI agents that can transact with each other — paying for services, settling agreements, moving value — without human intervention at the transaction level. But most demos cheat: they run both agents in the same process with shared memory, which doesn't prove anything about real-world agent interoperability.

The hard questions are: Can two agents that don't share a runtime discover each other over a network? Can they exchange the information needed to transact? Can they independently manage wallets and verify that a transfer actually happened on-chain?

This POC exists to answer those questions with two truly independent agents in separate containers, communicating over HTTP, transacting on Solana devnet — with a dashboard that makes the whole flow visible and interactive.

## 3. Goals & Success Metrics

**Primary Goal:** Prove that two independent, containerized LangChain agents can discover each other over a network, exchange wallet addresses, and complete a SOL transfer on devnet — observable and triggerable from a web dashboard.

| Metric | Target |
|---|---|
| End-to-end transfer completes between two containers | Yes/No — must work reliably |
| Agents discover each other and exchange addresses via messaging | No hardcoded addresses in transfer logic |
| Transaction confirmed on-chain (devnet explorer) | Verifiable via Solana Explorer |
| Agent A's balance decreases by transfer amount | Exact match (minus tx fee) |
| Agent B's balance increases by transfer amount | Exact match |
| Time from agent initiation to on-chain confirmation | < 60 seconds (includes messaging overhead) |
| Transfer succeeds on 9 out of 10 consecutive runs | ≥ 90% reliability |
| Dashboard reflects updated balances within 5 seconds of confirmation | Real-time feedback |
| User can trigger a transfer from the UI and see it complete | Interactive demo works |

**Non-Goals (for this POC):**
- Production-grade security or key management
- Mainnet deployment
- Complex negotiation or multi-step commerce
- Agent identity verification or trust frameworks

## 4. Target Users

This is an internal technical POC. The "users" are:

- **You / your engineering team** — evaluating whether this architecture works and is worth building on
- **Future decision-makers** — who will see the results and decide whether to fund further development
- **Demo audience** — anyone you walk through the POC using the dashboard

## 5. User Stories / Use Cases

### Must Have

- **As a developer**, I want to start the full system with `docker-compose up` and have two agents and a dashboard come online, each agent initializing its own Solana devnet wallet independently.
- **As a developer**, I want Agent A to discover Agent B over the network and request Agent B's wallet address via HTTP, so I can prove agents can coordinate without a shared config.
- **As a developer**, I want Agent A to initiate a SOL transfer to Agent B's discovered address using a natural language command, so I can prove the agent translates intent into a blockchain transaction.
- **As a developer**, I want Agent B to detect the incoming transfer and confirm receipt, so I can prove both agents independently verify the on-chain state.
- **As a developer**, I want to see the full message exchange and transaction details logged by both agents, so I can trace the entire flow.
- **As a demo user**, I want to open a web dashboard that shows both agents' wallet addresses and SOL balances in real time.
- **As a demo user**, I want to click a "Send" button specifying an amount and direction (A→B or B→A), have the transfer routed through the agent layer, and see the balances update on screen.
- **As a demo user**, I want to see a transaction log on the dashboard showing recent transfers with timestamps, amounts, and Solana Explorer links.

### Should Have

- **As a developer**, I want the system to handle common failures gracefully (agent unreachable, insufficient balance, network timeout), and surface errors in the dashboard.
- **As a developer**, I want to also demonstrate an SPL token transfer (not just native SOL), so I can prove the system works with custom tokens.
- **As a demo user**, I want a visual indicator (spinner, status badge) showing when a transfer is in progress.

### Nice to Have

- **As a developer**, I want a structured agent-to-agent protocol (request payment → share address → confirm transfer → acknowledge receipt) so I can show a repeatable transaction handshake.
- **As a demo user**, I want to see a live activity feed showing the agent-to-agent messages as they happen (request_address, share_address, notify_transfer, confirm_receipt).

## 6. Functional Requirements

### 6.1 Wallet Management

- FR-1: Each agent must generate or load a Solana keypair on container startup, independent of the other agent.
- FR-2: Each agent must be able to query its own wallet balance (SOL and SPL tokens).
- FR-3: Wallet keypairs must be persisted via Docker volumes so they survive container restarts.
- FR-4: On first run, each agent must automatically request an airdrop of devnet SOL to fund its wallet.

### 6.2 Agent Orchestration

- FR-5: Each agent must be implemented using LangChain or LangGraph, running as an independent process in its own container.
- FR-6: Each agent must have access to Solana wallet tools (balance check, transfer) as LangChain tools.
- FR-7: Each agent must also have access to messaging tools (send message, receive message) as LangChain tools.
- FR-8: Agents must accept transfer commands from the dashboard via their HTTP API and autonomously handle the full flow: discover the other agent, request its address, execute the transfer, and confirm.

### 6.3 Agent-to-Agent Messaging

- FR-9: Each agent must expose a lightweight HTTP API (e.g., FastAPI or Flask) for receiving messages from other agents and commands from the dashboard.
- FR-10: The messaging protocol must support at minimum: `request_address`, `share_address`, `notify_transfer`, and `confirm_receipt` message types.
- FR-11: Agents must discover each other via a known service endpoint (Docker Compose service names, e.g., `http://agent-b:8000`). Full dynamic discovery is out of scope for this POC.
- FR-12: All inter-agent messages must be logged with timestamps by both sender and receiver.

### 6.4 Token Transfer

- FR-13: The system must support native SOL transfers between the two agent wallets.
- FR-14: The system must construct, sign, and submit a Solana transaction programmatically.
- FR-15: The system must wait for transaction confirmation and return the transaction signature.
- FR-16: The system must log: sender address, receiver address, amount, transaction signature, and confirmation status.

### 6.5 Web Dashboard

- FR-17: The dashboard must run in a separate Docker container, accessible at `http://localhost:3000`.
- FR-18: The dashboard must display each agent's wallet address (truncated with copy-to-clipboard) and current SOL balance.
- FR-19: Balances must auto-refresh on a polling interval (every 5 seconds) or update via WebSocket push from the agents.
- FR-20: The dashboard must provide a transfer form: select direction (Agent A → Agent B or Agent B → Agent A), enter amount, and click "Send."
- FR-21: Clicking "Send" must route the command to the sending agent's HTTP API, which triggers the full agent-driven flow (discovery, address exchange, transfer, confirmation).
- FR-22: The dashboard must show transfer status: idle → in progress (spinner) → success (with tx hash link) or error (with message).
- FR-23: The dashboard must display a transaction history table showing: timestamp, direction, amount, transaction signature (linked to Solana Explorer), and status.
- FR-24: The dashboard must be a single-page app (React, Vue, or plain HTML/JS — whichever is fastest to build).

### 6.6 Dashboard–Agent API

- FR-25: Each agent must expose the following HTTP endpoints for the dashboard:
  - `GET /status` — returns agent health, wallet address, and current SOL balance
  - `POST /transfer` — accepts `{to_agent: string, amount: number}` and triggers the agent-driven transfer flow
  - `GET /transactions` — returns recent transaction history for this agent
- FR-26: The dashboard must aggregate data from both agents' `/status` endpoints to build its display.

### 6.7 SPL Token Support (Should Have)

- FR-27: The system must support creating a test SPL token on devnet.
- FR-28: The system must support transferring SPL tokens between agent wallets.
- FR-29: The system must handle associated token account creation if the recipient doesn't have one.
- FR-30: If SPL tokens are supported, the dashboard must display SPL token balances alongside SOL.

### 6.8 Observability

- FR-31: All agent actions, tool calls, and inter-agent messages must be logged to stdout with timestamps.
- FR-32: Each agent must print a summary after a transfer: its own before/after balance, transaction signature, and a devnet explorer link.
- FR-33: Docker Compose must aggregate logs from all three containers so the full interaction is visible in one terminal.

## 7. Non-Functional Requirements

- **Network:** All blockchain transactions on Solana devnet only. No mainnet interaction.
- **Isolation:** Each agent runs in its own Docker container with no shared filesystem or memory. The dashboard is a third container. Communication only via HTTP and Solana devnet.
- **Performance:** End-to-end transfer (including discovery and messaging) should complete in under 60 seconds. Dashboard balance refresh within 5 seconds of confirmation.
- **Reliability:** The system should handle transient network errors with basic retry logic (up to 3 retries) for both inter-agent messaging and Solana RPC calls.
- **Security:** Keypairs stored as files in Docker volumes. Acceptable for POC — flag for redesign before any mainnet work. Dashboard has no authentication (local-only access is fine for POC).
- **Dependencies:** Must run on a standard development machine with Docker and Docker Compose installed.

## 8. Scope & Constraints

### In Scope (v0.1 — this POC)

- Two agents in separate Docker containers, devnet only
- Web dashboard in a third Docker container
- Agent-to-agent HTTP messaging for address exchange and transfer coordination
- Dashboard-to-agent HTTP API for triggering transfers and reading state
- Native SOL transfer (must have) and SPL token transfer (should have)
- LangChain/LangGraph agent framework
- Docker Compose for orchestration
- Solana Python SDK (solders/solana-py)

### Out of Scope

- Mainnet deployment or real funds
- Dynamic agent discovery (mDNS, registry service, DHT)
- Multi-agent negotiation or pricing logic
- Persistent agent state across `docker-compose down` cycles
- Dashboard authentication or multi-user support
- Production key management (HSM, vault, MPC)
- Agent authentication, identity verification, or trust
- Compliance, KYC, or regulatory considerations
- Encrypted agent-to-agent communication (TLS between containers)
- Mobile-responsive dashboard design

### Constraints

- Devnet has rate limits on airdrops (~2 SOL per request, throttled during high traffic)
- LLM API costs for agent reasoning (minimal for a POC, but non-zero)
- Solana devnet can be unstable during high-traffic periods
- Docker networking adds minor latency vs. single-process
- Dashboard polling adds minor load on agent APIs

## 9. Dependencies & Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Solana devnet instability / airdrop throttling | Medium | Medium | Persist wallets via Docker volumes; retry logic |
| Inter-agent messaging failures (container networking) | Medium | Medium | Docker Compose handles DNS; add health checks and retries |
| LangChain tool integration complexity with Solana SDK | Medium | High | Prototype Solana tools standalone first, then wrap as LangChain tools |
| Agent hallucinates wallet addresses or amounts | Low | High | Validate all addresses and amounts before signing; use structured tool outputs |
| Docker Compose port/network conflicts | Low | Low | Use dedicated Docker network; document port assignments |
| Race conditions in message exchange | Medium | Medium | Use synchronous request-response pattern; add timeouts |
| Dashboard shows stale data after transfer | Low | Medium | Poll frequently (5s) or use WebSocket for push updates |
| CORS issues between dashboard and agent APIs | Medium | Low | Configure CORS headers on agent HTTP APIs |
| LLM latency compounds with messaging latency | Low | Low | Acceptable for POC; 60-second budget is generous |

## 10. Timeline & Milestones

| Milestone | Description | Est. Effort |
|---|---|---|
| M1: Wallet tooling | Generate keypairs, check balances, request airdrops — working standalone | 0.5 days |
| M2: SOL transfer tool | Build and test the transfer function outside of any agent framework | 0.5 days |
| M3: Agent messaging API | Build the HTTP messaging layer (FastAPI) with the 4 message types + dashboard endpoints | 0.5 days |
| M4: LangChain integration | Wrap wallet + messaging tools as LangChain tools, build two agent configs | 1 day |
| M5: Web dashboard | Build the SPA: wallet display, transfer form, transaction history, status indicators | 1 day |
| M6: Dockerize | Create Dockerfiles for all three containers, Docker Compose config, volume mounts, networking | 0.5 days |
| M7: End-to-end demo | Full flow from dashboard click → agent transfer → balance update | 0.5 days |
| M8: SPL token support | Add SPL token minting, transfer, and dashboard display (stretch) | 0.5 days |

**Total estimated effort: 4–5 days**

## 11. Open Questions

1. **Which LLM?** GPT-4, Claude, or a smaller model for the agent reasoning? For a POC, any capable model works — cost is minimal. Both agents can use the same LLM provider.
2. **Persist wallets across restarts?** Docker volumes will persist keypairs across container restarts, but should they survive a full `docker-compose down`? Recommendation: yes, use named volumes.
3. **SPL token scope:** Mint a custom test token, or use an existing devnet token? Custom mint gives full control.
4. **Message format:** Plain JSON over HTTP is simplest. Should we use a more structured protocol (e.g., DIDComm, Agent Protocol) to future-proof? Recommendation: plain JSON for POC, note the upgrade path.
5. **Error recovery:** If the transfer succeeds on-chain but the confirmation message to Agent B fails, what happens? For POC, Agent B can independently verify by checking its balance. Worth documenting as a known limitation.
6. **Dashboard framework:** React is the most common choice. Plain HTML/JS with no build step would be faster to ship. Recommendation: React if you want to extend it later, plain HTML/JS if speed is the priority.
7. **Real-time updates:** Polling (simple, no extra infra) or WebSocket (better UX, more plumbing)? Recommendation: start with polling, add WebSocket as a nice-to-have.
