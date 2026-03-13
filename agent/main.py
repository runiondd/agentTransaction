import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from api.routes import router


class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter with agent_id on every line."""

    def format(self, record):
        log = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "agent": config.AGENT_ID,
            "level": record.levelname,
            "module": record.module,
            "msg": record.getMessage(),
        }
        return json.dumps(log)


handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)

# Quiet noisy HTTP request logs from httpx/httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {config.AGENT_ID} on port {config.AGENT_PORT}")

    # Initialize wallet
    from wallet.manager import WalletManager

    wallet = WalletManager.get_instance()
    wallet.init_wallet()

    # Airdrop if balance is 0
    try:
        balance = wallet.get_balance()
        logger.info(f"Current balance: {balance} SOL")
        if balance == 0:
            wallet.request_airdrop(2.0)
    except Exception as e:
        logger.warning(f"Could not check balance or airdrop: {e}")

    yield
    logger.info(f"Shutting down {config.AGENT_ID}")


app = FastAPI(title=f"Solana Agent - {config.AGENT_ID}", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=config.AGENT_PORT)
