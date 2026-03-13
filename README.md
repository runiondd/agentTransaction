# AI Agent-to-Agent Solana Token Transfer

Two independent AI agents in separate Docker containers discover each other, exchange wallet addresses, and execute SOL transfers on Solana devnet — with a real-time web dashboard.

## Status

Phase 3 complete. Code built, all components implemented.

## Architecture

- **Agent A & B**: Python FastAPI + LangChain agents with Solana wallet tools
- **Dashboard**: React + Vite + Tailwind CSS SPA
- **Blockchain**: Solana devnet
- **Orchestration**: Docker Compose

See [architecture.md](architecture.md) for full technical design.

## Project Documents

| Document | Status | Description |
|----------|--------|-------------|
| [PRD](prd.md) | Complete | Product requirements and acceptance criteria |
| [Architecture](architecture.md) | Complete | Technical design and system architecture |
| [Tasks](tasks.md) | Complete | Ordered build task breakdown |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- An Anthropic API key

### Setup

```bash
# Clone the repo
git clone https://github.com/runiondd/agentTransaction.git
cd agentTransaction

# Create .env with your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start everything
docker compose up --build
```

### Usage

1. Open **http://localhost:3000** for the dashboard
2. Both agents will auto-initialize wallets and airdrop 2 SOL from devnet
3. Use the transfer form to send SOL between agents
4. Watch balances update and transactions appear in the history table
5. Click transaction signatures to verify on Solana Explorer

### Ports

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| Agent A API | http://localhost:8001 |
| Agent B API | http://localhost:8002 |

### Agent API Endpoints

- `GET /status` — Health, wallet address, SOL balance
- `POST /transfer` — Trigger agent-driven transfer `{to_agent, amount}`
- `GET /transactions` — Transaction history
- `POST /message` — Inter-agent messaging

### Logs

```bash
docker compose logs -f        # All containers
docker compose logs -f agent-a  # Single agent
```

## How It Works

1. Dashboard sends `POST /transfer` to the sending agent
2. LangChain agent reasons about the task using Claude
3. Agent requests peer's wallet address via HTTP messaging
4. Agent constructs, signs, and submits a Solana transfer transaction
5. Agent notifies peer of the transfer
6. Peer verifies the transaction on-chain and confirms receipt
7. Dashboard polls both agents and updates balances

## Known Limitations

- Devnet only — no mainnet support
- No authentication on APIs or dashboard
- Wallets stored as JSON files (not production-grade key management)
- Devnet airdrops can be throttled during high traffic
- In-memory transaction log (lost on container restart)
