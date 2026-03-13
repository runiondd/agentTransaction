# AI Agent-to-Agent Solana Token Transfer — Task Breakdown

## Milestone 1: Project Scaffolding & Wallet Foundation

### Task 1.1: Initialize Project Structure
- **Description:** Create the monorepo directory structure, initialize Python project for the agent, initialize React+Vite project for the dashboard, and create the Docker Compose skeleton.
- **Files to create:**
  - `docker-compose.yml` (skeleton with service stubs)
  - `agent/Dockerfile`
  - `agent/requirements.txt`
  - `agent/main.py` (FastAPI hello-world)
  - `agent/config.py` (env-based config with defaults)
  - `agent/api/__init__.py`
  - `agent/api/routes.py` (health check endpoint only)
  - `agent/agent/__init__.py`
  - `agent/agent/tools/__init__.py`
  - `agent/wallet/__init__.py`
  - `agent/models/__init__.py`
  - `agent/models/schemas.py` (empty Pydantic models file)
  - `dashboard/package.json`
  - `dashboard/Dockerfile`
  - `dashboard/vite.config.js`
  - `dashboard/tailwind.config.js`
  - `dashboard/index.html`
  - `dashboard/src/main.jsx`
  - `dashboard/src/App.jsx` (placeholder)
  - `README.md`
  - `.env.example`
  - `.gitignore`
- **Depends on:** Nothing
- **Done when:** `docker-compose up` starts all three containers without errors. Agent returns `{"status": "ok"}` on `GET /status`. Dashboard serves a blank page at `localhost:3000`.

### Task 1.2: Wallet Manager — Keypair Generation & Loading
- **Description:** Implement the wallet manager that generates a new Solana keypair on first run or loads an existing one from the volume-mounted file path. Use solders for keypair operations.
- **PRD Requirements:** FR-1, FR-3
- **Files to create:**
  - `agent/wallet/manager.py`
- **Files to modify:**
  - `agent/main.py` (add wallet init to FastAPI lifespan)
  - `agent/config.py` (add WALLET_PATH config)
  - `agent/requirements.txt` (add solders, solana)
- **Depends on:** Task 1.1
- **Acceptance Criteria:**
  - Agent generates a new Solana keypair if no keypair file exists at WALLET_PATH
  - Agent loads an existing keypair if the file exists
  - Keypair is persisted to the volume-mounted path as JSON
  - Wallet address (Base58 public key) is available via `WalletManager.address`
  - Keypair survives container restart (Docker volume)
- **Done when:** Agent starts, logs its wallet address, and the same address appears after container restart.

### Task 1.3: Wallet Manager — Balance Queries & Airdrop
- **Description:** Add balance querying and devnet airdrop functionality to the wallet manager. On first run (when balance is 0), automatically request a devnet airdrop.
- **PRD Requirements:** FR-2, FR-4
- **Files to modify:**
  - `agent/wallet/manager.py` (add get_balance, request_airdrop methods)
  - `agent/main.py` (add airdrop logic to lifespan startup)
  - `agent/config.py` (add SOLANA_RPC_URL config)
- **Depends on:** Task 1.2
- **Acceptance Criteria:**
  - `get_balance()` returns current SOL balance from Solana devnet RPC
  - `request_airdrop(amount)` requests devnet SOL and waits for confirmation
  - On startup, if balance is 0, agent automatically airdrops 2 SOL
  - Balance queries include basic retry logic (3 attempts) for transient RPC errors
- **Done when:** Agent starts, airdrops SOL if needed, and logs its balance. Balance matches what Solana Explorer shows.

### Task 1.4: Status Endpoint with Wallet Data
- **Description:** Update the `/status` endpoint to return full wallet information: agent ID, health, wallet address, and SOL balance.
- **PRD Requirements:** FR-25 (GET /status), FR-26
- **Files to modify:**
  - `agent/api/routes.py` (update /status handler)
  - `agent/models/schemas.py` (add StatusResponse model)
- **Depends on:** Task 1.3
- **Acceptance Criteria:**
  - `GET /status` returns `{agent_id, healthy, wallet_address, sol_balance, peer_agent_url}`
  - All fields populated from live wallet data and config
  - Response matches the Pydantic schema
- **Done when:** Both agent containers return correct status JSON with real wallet addresses and balances.

---

## Milestone 2: Solana Transfer Engine

### Task 2.1: SOL Transfer Function
- **Description:** Implement the core SOL transfer function: construct a transfer transaction, sign it with the agent's keypair, submit it to Solana devnet, and wait for confirmation.
- **PRD Requirements:** FR-13, FR-14, FR-15
- **Files to create:**
  - `agent/wallet/transfer.py`
- **Files to modify:**
  - `agent/wallet/manager.py` (add transfer method that delegates to transfer.py)
  - `agent/models/schemas.py` (add TransferResult model)
- **Depends on:** Task 1.3
- **Acceptance Criteria:**
  - `transfer_sol(recipient_address, amount)` constructs a SystemProgram.transfer instruction
  - Transaction is signed with the agent's keypair
  - Transaction is submitted to devnet RPC and confirmed
  - Returns transaction signature and confirmation status
  - Validates recipient address is valid Base58 before signing
  - Validates amount is positive and does not exceed balance
  - Includes retry logic (3 attempts) for RPC submission
- **Done when:** A standalone test transfers SOL between two keypairs and the transaction is visible on Solana Explorer.

### Task 2.2: Transaction Logging
- **Description:** Implement in-memory transaction logging and the `/transactions` endpoint.
- **PRD Requirements:** FR-16, FR-25 (GET /transactions)
- **Files to create:**
  - `agent/state.py` (in-memory state: transaction log, peer cache)
- **Files to modify:**
  - `agent/wallet/manager.py` (log transactions after transfer)
  - `agent/api/routes.py` (add /transactions endpoint)
  - `agent/models/schemas.py` (add TransactionRecord, TransactionsResponse models)
- **Depends on:** Task 2.1
- **Acceptance Criteria:**
  - Every transfer (sent or received) is recorded with: id, timestamp, direction, counterparty, amount, signature, status, explorer_url
  - `GET /transactions` returns the transaction log as JSON
  - Explorer URL uses devnet cluster parameter
- **Done when:** After a transfer, `/transactions` returns the record with a working Solana Explorer link.

---

## Milestone 3: Inter-Agent Messaging

### Task 3.1: Message Schema & Endpoint
- **Description:** Define the inter-agent message protocol and implement the `/message` endpoint that handles incoming messages from the peer agent.
- **PRD Requirements:** FR-9, FR-10, FR-12
- **Files to modify:**
  - `agent/models/schemas.py` (add AgentMessage model with type enum and payload)
  - `agent/api/routes.py` (add POST /message endpoint)
- **Depends on:** Task 1.4
- **Acceptance Criteria:**
  - `POST /message` accepts AgentMessage with types: `request_address`, `share_address`, `notify_transfer`, `confirm_receipt`
  - `request_address` → responds with `share_address` containing this agent's wallet address
  - `notify_transfer` → agent verifies the transaction on-chain, responds with `confirm_receipt`
  - All incoming and outgoing messages are logged with timestamps and agent IDs
  - Invalid message types return 400
- **Done when:** Agent A can POST a `request_address` message to Agent B's `/message` endpoint and receive Agent B's wallet address in response.

### Task 3.2: Messaging Client
- **Description:** Build an HTTP client that agents use to send messages to their peer. This will be wrapped as a LangChain tool in the next milestone.
- **PRD Requirements:** FR-11, FR-12
- **Files to create:**
  - `agent/agent/tools/messaging.py` (messaging client functions, not yet LangChain tools)
- **Files to modify:**
  - `agent/config.py` (ensure PEER_AGENT_URL is available)
  - `agent/requirements.txt` (add httpx for async HTTP client)
- **Depends on:** Task 3.1
- **Acceptance Criteria:**
  - `request_peer_address(peer_url)` sends `request_address` and returns the peer's wallet address
  - `notify_transfer(peer_url, signature, amount, from_address)` sends `notify_transfer` and returns confirmation status
  - Uses httpx with timeout (30s) and retry logic (3 attempts)
  - All sent messages are logged with timestamps
- **Done when:** Agent A can programmatically request Agent B's address and get a response over the Docker network.

---

## Milestone 4: LangChain Agent Integration

### Task 4.1: Wallet LangChain Tools
- **Description:** Wrap the wallet operations as LangChain tools that the agent can invoke during reasoning.
- **PRD Requirements:** FR-6
- **Files to create:**
  - `agent/agent/tools/wallet.py` (LangChain @tool definitions)
- **Files to modify:**
  - `agent/requirements.txt` (add langchain, langchain-anthropic, langchain-core)
- **Depends on:** Task 2.1, Task 1.3
- **Acceptance Criteria:**
  - `check_balance` tool returns current SOL balance and wallet address
  - `transfer_sol` tool accepts recipient address and amount, executes transfer, returns result
  - `get_wallet_address` tool returns this agent's wallet address
  - All tools have clear docstrings that help the LLM understand when/how to use them
  - Tools validate inputs and return human-readable error messages on failure
- **Done when:** Tools can be invoked standalone (outside agent loop) and return correct results.

### Task 4.2: Messaging LangChain Tools
- **Description:** Wrap the messaging client functions as LangChain tools.
- **PRD Requirements:** FR-7
- **Files to modify:**
  - `agent/agent/tools/messaging.py` (convert functions to LangChain @tool definitions)
- **Depends on:** Task 3.2
- **Acceptance Criteria:**
  - `request_peer_address` tool sends `request_address` to peer and returns their wallet address
  - `notify_peer_of_transfer` tool sends `notify_transfer` to peer and returns confirmation
  - Tools have clear docstrings
  - Tools handle and report errors gracefully
- **Done when:** Messaging tools can be invoked standalone and successfully communicate with the peer agent.

### Task 4.3: LangChain Agent Definition
- **Description:** Create the LangChain agent that uses Claude to reason about transfer tasks, selecting the right tools in the right order. Wire it into the `/transfer` endpoint.
- **PRD Requirements:** FR-5, FR-8
- **Files to create:**
  - `agent/agent/agent.py` (agent definition, tool registration, execution function)
- **Files to modify:**
  - `agent/api/routes.py` (wire POST /transfer to invoke the agent)
  - `agent/config.py` (add ANTHROPIC_API_KEY config)
  - `agent/requirements.txt` (verify langchain-anthropic version)
- **Depends on:** Task 4.1, Task 4.2
- **Acceptance Criteria:**
  - Agent uses `ChatAnthropic` with Claude as the LLM
  - Agent has access to all 5 tools: check_balance, transfer_sol, get_wallet_address, request_peer_address, notify_peer_of_transfer
  - System prompt instructs agent to: (1) request peer address, (2) check balance, (3) transfer SOL, (4) notify peer
  - `POST /transfer {to_agent, amount}` triggers the agent which autonomously completes the full flow
  - Agent execution is logged (verbose=True) showing reasoning and tool calls
  - Agent completes the flow in under 60 seconds
- **Done when:** Calling `POST /transfer` on Agent A causes it to autonomously discover Agent B's address, transfer SOL, and notify Agent B — all visible in logs.

### Task 4.4: Transaction Verification on Receive
- **Description:** When Agent B receives a `notify_transfer` message, it should verify the transaction on-chain before confirming receipt. Also record received transfers in the transaction log.
- **PRD Requirements:** FR-16 (logging received transfers)
- **Files to modify:**
  - `agent/wallet/manager.py` (add verify_transaction method)
  - `agent/api/routes.py` (update /message handler for notify_transfer to verify and log)
  - `agent/state.py` (log received transfers)
- **Depends on:** Task 3.1, Task 2.2
- **Acceptance Criteria:**
  - When `notify_transfer` is received, agent queries Solana for the transaction by signature
  - Verifies the transaction exists and is confirmed
  - Logs the received transfer in the transaction log with direction="received"
  - Returns `confirm_receipt` with `confirmed: true/false`
- **Done when:** After a transfer, both Agent A's and Agent B's `/transactions` endpoints show the transfer (sent and received respectively).

---

## Milestone 5: Web Dashboard

### Task 5.1: Dashboard Scaffolding & API Client
- **Description:** Set up the React app with routing, Tailwind CSS, and the API client for communicating with both agents.
- **PRD Requirements:** FR-17, FR-24
- **Files to modify:**
  - `dashboard/src/App.jsx` (basic layout structure)
  - `dashboard/src/main.jsx` (ensure React renders)
  - `dashboard/tailwind.config.js` (configure content paths)
  - `dashboard/package.json` (add dependencies: tailwindcss, autoprefixer, postcss)
  - `dashboard/index.html` (add Tailwind CDN or PostCSS setup)
- **Files to create:**
  - `dashboard/src/api/agents.js` (fetchAgentStatus, fetchTransactions, triggerTransfer)
  - `dashboard/postcss.config.js`
- **Depends on:** Task 1.1
- **Acceptance Criteria:**
  - React app builds and serves at localhost:3000
  - API client has functions for: GET /status, GET /transactions, POST /transfer
  - API client uses environment variables for agent URLs (VITE_AGENT_A_URL, VITE_AGENT_B_URL)
  - Basic layout renders with a title/header
- **Done when:** Dashboard loads in browser, API client functions exist (can be tested with mock data).

### Task 5.2: Wallet Cards with Polling
- **Description:** Build the WalletCard component and the polling hook that fetches each agent's status every 5 seconds.
- **PRD Requirements:** FR-18, FR-19, FR-26
- **Files to create:**
  - `dashboard/src/components/WalletCard.jsx`
  - `dashboard/src/hooks/useAgentStatus.js`
- **Files to modify:**
  - `dashboard/src/App.jsx` (add two WalletCard components)
- **Depends on:** Task 5.1, Task 1.4
- **Acceptance Criteria:**
  - Each WalletCard shows: agent name, wallet address (truncated to first 4 + last 4 chars), copy-to-clipboard button, SOL balance
  - Balance updates every 5 seconds via polling
  - Shows a loading state while first fetch is in progress
  - Shows an error state if agent is unreachable
- **Done when:** Dashboard shows two wallet cards with live balances from both running agent containers.

### Task 5.3: Transfer Form
- **Description:** Build the transfer form with direction selector, amount input, send button, and status indicator.
- **PRD Requirements:** FR-20, FR-21, FR-22
- **Files to create:**
  - `dashboard/src/components/TransferForm.jsx`
- **Files to modify:**
  - `dashboard/src/App.jsx` (add TransferForm between wallet cards)
- **Depends on:** Task 5.1
- **Acceptance Criteria:**
  - Direction dropdown/toggle: "Agent A → Agent B" or "Agent B → Agent A"
  - Amount input: numeric, validates positive number
  - Send button: triggers POST /transfer on the sending agent
  - Status display: idle → "Sending..." (spinner) → "Success! Tx: [linked hash]" or "Error: [message]"
  - Send button is disabled while a transfer is in progress
  - After successful transfer, triggers a balance refresh
- **Done when:** User can select direction, enter amount, click Send, see spinner, and see success/error status.

### Task 5.4: Transaction History Table
- **Description:** Build the transaction table that shows recent transfers from both agents.
- **PRD Requirements:** FR-23
- **Files to create:**
  - `dashboard/src/components/TransactionTable.jsx`
  - `dashboard/src/hooks/useTransactions.js`
- **Files to modify:**
  - `dashboard/src/App.jsx` (add TransactionTable below transfer form)
- **Depends on:** Task 5.1, Task 2.2
- **Acceptance Criteria:**
  - Table columns: Timestamp, Direction (A→B or B→A), Amount (SOL), Tx Signature (linked to Solana Explorer), Status
  - Aggregates transactions from both agents, deduplicates by signature
  - Sorted by timestamp descending (most recent first)
  - Polls every 5 seconds for new transactions
  - Signature is truncated but links to full Solana Explorer devnet URL
- **Done when:** After a transfer, the transaction appears in the table with a working Explorer link.

---

## Milestone 6: Dockerization & End-to-End

### Task 6.1: Agent Dockerfile & Build
- **Description:** Finalize the agent Dockerfile and ensure both agent containers build and run correctly with all dependencies.
- **PRD Requirements:** FR-5 (independent containers), FR-3 (volume persistence)
- **Files to modify:**
  - `agent/Dockerfile` (finalize: Python base, install deps, copy code, entrypoint)
  - `agent/requirements.txt` (pin all dependency versions)
- **Depends on:** Task 4.3
- **Acceptance Criteria:**
  - `docker build ./agent` succeeds without errors
  - Container starts, initializes wallet, airdrops SOL, and serves API
  - Keypair persists via named Docker volume
  - Health check endpoint works for Docker Compose depends_on
- **Done when:** Both agent containers build from the same Dockerfile and start independently with different configs.

### Task 6.2: Dashboard Dockerfile & Build
- **Description:** Finalize the dashboard Dockerfile with a multi-stage build (build React app, serve with nginx or lightweight server).
- **PRD Requirements:** FR-17
- **Files to modify:**
  - `dashboard/Dockerfile` (multi-stage: node build → nginx serve)
- **Files to create:**
  - `dashboard/nginx.conf` (if using nginx to serve the SPA)
- **Depends on:** Task 5.4
- **Acceptance Criteria:**
  - `docker build ./dashboard` succeeds without errors
  - Container serves the React app at port 3000
  - Environment variables are baked in at build time (VITE_ vars)
- **Done when:** Dashboard container builds and serves the app correctly.

### Task 6.3: Docker Compose Full Stack
- **Description:** Finalize the Docker Compose configuration with networking, volumes, health checks, and dependency ordering.
- **PRD Requirements:** FR-33 (log aggregation)
- **Files to modify:**
  - `docker-compose.yml` (finalize all services, networks, volumes, health checks)
- **Files to create:**
  - `.env.example` (document required environment variables)
- **Depends on:** Task 6.1, Task 6.2
- **Acceptance Criteria:**
  - `docker-compose up` starts all three containers
  - Agents start first, dashboard waits for agent health checks
  - Agents can communicate via Docker network (agent-a can reach agent-b:8000)
  - Dashboard can reach agents via host-mapped ports (localhost:8001, localhost:8002)
  - `docker-compose logs -f` shows aggregated logs from all containers
  - Named volumes persist wallet keypairs across restarts
- **Done when:** `docker-compose up` brings up the full system from scratch and all services are healthy.

### Task 6.4: End-to-End Smoke Test
- **Description:** Perform and document a full end-to-end test: start the system, open the dashboard, trigger a transfer, verify balances update, check transaction history, verify on Solana Explorer.
- **PRD Requirements:** All success metrics from Section 3
- **Files to create:**
  - `agent/tests/test_e2e.py` (automated end-to-end test script)
- **Depends on:** Task 6.3
- **Acceptance Criteria:**
  - `docker-compose up` starts cleanly
  - Dashboard shows both wallets with balances > 0
  - Trigger A→B transfer of 0.5 SOL from dashboard
  - Transfer completes (spinner → success) within 60 seconds
  - Agent A balance decreases by ~0.5 SOL (plus tx fee)
  - Agent B balance increases by 0.5 SOL
  - Transaction appears in history table with Explorer link
  - Explorer link shows confirmed transaction on devnet
  - Repeat B→A transfer to verify both directions work
  - Run 10 consecutive transfers; ≥ 9 succeed (90% reliability)
- **Done when:** All success metrics from PRD Section 3 are verified and passing.

---

## Milestone 7: Observability & Polish

### Task 7.1: Structured Logging
- **Description:** Ensure all agents produce structured, timestamped logs for every significant action: startup, wallet init, airdrop, message sent/received, transfer initiated/confirmed, errors.
- **PRD Requirements:** FR-12, FR-16, FR-31, FR-32
- **Files to modify:**
  - `agent/main.py` (configure structured logging format)
  - `agent/api/routes.py` (add logging to all handlers)
  - `agent/wallet/manager.py` (add logging to wallet operations)
  - `agent/wallet/transfer.py` (add logging to transfer operations)
  - `agent/agent/agent.py` (ensure LangChain verbose output is captured)
- **Depends on:** Task 6.4
- **Acceptance Criteria:**
  - All logs include: timestamp, agent_id, action, relevant data
  - Transfer summary logged after each transfer: before/after balance, signature, explorer link
  - Inter-agent messages logged by both sender and receiver
  - Error states logged with context
- **Done when:** `docker-compose logs -f` shows a clear, readable narrative of the full transfer flow across both agents.

### Task 7.2: Error Handling & Edge Cases
- **Description:** Add graceful error handling for known failure modes: insufficient balance, peer unreachable, Solana RPC timeout, invalid amounts.
- **PRD Requirements:** Should Have — graceful failure handling, error surfacing in dashboard
- **Files to modify:**
  - `agent/api/routes.py` (error responses with meaningful messages)
  - `agent/wallet/manager.py` (handle insufficient balance)
  - `agent/agent/tools/messaging.py` (handle peer unreachable)
  - `agent/wallet/transfer.py` (handle RPC timeouts)
  - `dashboard/src/components/TransferForm.jsx` (display error messages from API)
- **Depends on:** Task 6.4
- **Acceptance Criteria:**
  - Transferring more than available balance returns clear error, not a crash
  - If peer agent is down, sender gets a timeout error within 30 seconds
  - Solana RPC failures trigger retry (3 attempts) then clear error
  - Dashboard shows error messages from failed transfers
  - No unhandled exceptions crash the agent container
- **Done when:** Each failure mode produces a clear error message visible in both logs and dashboard.

### Task 7.3: README & Setup Documentation
- **Description:** Write clear setup instructions so anyone can clone and run the POC.
- **Files to modify:**
  - `README.md`
- **Files to create:**
  - `.env.example` (if not already created)
- **Depends on:** Task 6.4
- **Acceptance Criteria:**
  - Prerequisites listed (Docker, Docker Compose, Anthropic API key)
  - Step-by-step setup: clone, create .env, docker-compose up
  - How to use the dashboard
  - How to read the logs
  - Known limitations documented
  - Architecture overview (link to architecture.md)
- **Done when:** A developer unfamiliar with the project can follow the README and have the system running within 10 minutes.

---

## Milestone 8: SPL Token Support (Stretch)

### Task 8.1: SPL Token Minting
- **Description:** Add the ability to mint a custom SPL token on devnet for testing.
- **PRD Requirements:** FR-27
- **Files to modify:**
  - `agent/wallet/manager.py` (add mint_spl_token method)
  - `agent/main.py` (optionally mint on startup if SPL testing is enabled)
  - `agent/config.py` (add SPL_TOKEN_ENABLED flag)
- **Depends on:** Task 2.1
- **Acceptance Criteria:**
  - Agent can create a new SPL token mint on devnet
  - Agent can mint tokens to its own associated token account
  - Token mint address is logged and available via /status
- **Done when:** Agent A has a custom SPL token balance visible on Solana Explorer.

### Task 8.2: SPL Token Transfer
- **Description:** Extend the transfer engine to support SPL token transfers, including creating associated token accounts for recipients.
- **PRD Requirements:** FR-28, FR-29
- **Files to modify:**
  - `agent/wallet/transfer.py` (add transfer_spl_token function)
  - `agent/wallet/manager.py` (add SPL balance query, ATA creation)
  - `agent/agent/tools/wallet.py` (add transfer_spl_token LangChain tool)
- **Depends on:** Task 8.1, Task 4.1
- **Acceptance Criteria:**
  - `transfer_spl_token(recipient, mint, amount)` creates recipient's ATA if needed, then transfers
  - Transaction is signed, submitted, and confirmed
  - Works through the LangChain agent flow (agent reasons about using SPL vs SOL tool)
- **Done when:** Agent A can transfer custom SPL tokens to Agent B via the agent flow.

### Task 8.3: Dashboard SPL Token Display
- **Description:** Update the dashboard to show SPL token balances alongside SOL.
- **PRD Requirements:** FR-30
- **Files to modify:**
  - `agent/api/routes.py` (add SPL balances to /status response)
  - `agent/models/schemas.py` (extend StatusResponse with spl_balances)
  - `dashboard/src/components/WalletCard.jsx` (display SPL token balances)
  - `dashboard/src/components/TransferForm.jsx` (add token type selector: SOL or SPL)
- **Depends on:** Task 8.2, Task 5.2
- **Acceptance Criteria:**
  - Wallet cards show SPL token balances below SOL balance
  - Transfer form has a token type selector when SPL is available
  - SPL transfers flow through the same agent-driven process
- **Done when:** Dashboard shows SPL balances and supports triggering SPL token transfers.

---

## PRD Requirement Coverage Matrix

| Requirement | Task(s) |
|---|---|
| FR-1: Keypair generation/loading | 1.2 |
| FR-2: Balance queries | 1.3 |
| FR-3: Keypair persistence (Docker volumes) | 1.2, 6.1 |
| FR-4: Devnet airdrop | 1.3 |
| FR-5: LangChain agent in own container | 4.3, 6.1 |
| FR-6: Solana wallet LangChain tools | 4.1 |
| FR-7: Messaging LangChain tools | 4.2 |
| FR-8: Accept commands, autonomous flow | 4.3 |
| FR-9: HTTP API for messages | 3.1 |
| FR-10: Message types (4 types) | 3.1 |
| FR-11: Discovery via Docker service names | 3.2 |
| FR-12: Message logging | 3.1, 3.2, 7.1 |
| FR-13: Native SOL transfers | 2.1 |
| FR-14: Transaction construction/signing | 2.1 |
| FR-15: Transaction confirmation | 2.1 |
| FR-16: Transfer logging | 2.2, 7.1 |
| FR-17: Dashboard in separate container | 5.1, 6.2 |
| FR-18: Wallet address + balance display | 5.2 |
| FR-19: Auto-refresh balances (polling) | 5.2 |
| FR-20: Transfer form (direction + amount) | 5.3 |
| FR-21: Send routes through agent | 5.3, 4.3 |
| FR-22: Transfer status display | 5.3 |
| FR-23: Transaction history table | 5.4 |
| FR-24: SPA dashboard | 5.1 |
| FR-25: Agent HTTP endpoints (/status, /transfer, /transactions) | 1.4, 4.3, 2.2 |
| FR-26: Dashboard aggregates from both agents | 5.2 |
| FR-27: SPL token minting | 8.1 |
| FR-28: SPL token transfer | 8.2 |
| FR-29: ATA creation | 8.2 |
| FR-30: Dashboard SPL display | 8.3 |
| FR-31: Structured logging | 7.1 |
| FR-32: Transfer summary logging | 7.1 |
| FR-33: Docker Compose log aggregation | 6.3 |
