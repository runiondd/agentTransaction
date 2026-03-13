import os


AGENT_ID = os.getenv("AGENT_ID", "agent-a")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8000"))
PEER_AGENT_URL = os.getenv("PEER_AGENT_URL", "http://agent-b:8000")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
WALLET_PATH = os.getenv("WALLET_PATH", "/data/keypair.json")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
