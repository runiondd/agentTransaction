import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException

import config
from models.schemas import (
    AgentMessage,
    StatusResponse,
    TransactionsResponse,
    TransferRequest,
    TransferResponse,
)
from state import app_state
from wallet.manager import WalletManager
from wallet.transfer import verify_transaction

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def get_status():
    wallet = WalletManager.get_instance()
    try:
        balance = wallet.get_balance()
    except Exception:
        balance = None

    return StatusResponse(
        agent_id=config.AGENT_ID,
        healthy=True,
        wallet_address=wallet.address if wallet.keypair else None,
        sol_balance=balance,
        peer_agent_url=config.PEER_AGENT_URL,
    )


@router.get("/transactions", response_model=TransactionsResponse)
async def get_transactions():
    return TransactionsResponse(transactions=app_state.get_transactions())


@router.post("/transfer", response_model=TransferResponse, status_code=202)
async def initiate_transfer(request: TransferRequest, background_tasks: BackgroundTasks):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    import uuid

    transfer_id = str(uuid.uuid4())

    background_tasks.add_task(_run_transfer, transfer_id, request.to_agent, request.amount)

    return TransferResponse(transfer_id=transfer_id, status="initiated")


async def _run_transfer(transfer_id: str, to_agent: str, amount: float):
    """Run the agent-driven transfer flow."""
    try:
        from agent.agent import run_transfer_agent

        await run_transfer_agent(to_agent, amount)
    except ImportError:
        # Fallback: direct transfer without LangChain agent (for early milestones)
        logger.info("LangChain agent not available, using direct transfer")
        await _direct_transfer(to_agent, amount)
    except Exception as e:
        logger.error(f"Transfer failed: {e}")


async def _direct_transfer(to_agent: str, amount: float):
    """Direct transfer without LangChain agent — used before agent integration."""
    import httpx

    wallet = WalletManager.get_instance()

    # Request peer address
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{config.PEER_AGENT_URL}/message",
                json={
                    "type": "request_address",
                    "sender": config.AGENT_ID,
                    "payload": {},
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                },
            )
            resp.raise_for_status()
            msg = resp.json()
            peer_address = msg["payload"]["wallet_address"]
    except Exception as e:
        logger.error(f"Failed to get peer address: {e}")
        return

    # Execute transfer
    from wallet.transfer import transfer_sol as do_transfer

    result = do_transfer(wallet.rpc_client, wallet.keypair, peer_address, amount)

    # Log the transaction
    app_state.add_transaction(
        direction="sent",
        counterparty=peer_address,
        amount=amount,
        signature=result.signature,
        status=result.status,
    )

    # Notify peer
    if result.status == "confirmed":
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{config.PEER_AGENT_URL}/message",
                    json={
                        "type": "notify_transfer",
                        "sender": config.AGENT_ID,
                        "payload": {
                            "signature": result.signature,
                            "amount": amount,
                            "from_address": wallet.address,
                        },
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    },
                )
        except Exception as e:
            logger.warning(f"Failed to notify peer of transfer: {e}")

    logger.info(
        f"Transfer complete: {amount} SOL to {peer_address} "
        f"status={result.status} sig={result.signature}"
    )


@router.post("/message")
async def receive_message(message: AgentMessage):
    """Handle incoming inter-agent messages."""
    logger.info(f"Received {message.type} from {message.sender}")

    wallet = WalletManager.get_instance()

    if message.type == "request_address":
        return AgentMessage(
            type="share_address",
            sender=config.AGENT_ID,
            payload={"wallet_address": wallet.address},
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    elif message.type == "share_address":
        app_state.peer_address = message.payload.get("wallet_address")
        return {"status": "ok"}

    elif message.type == "notify_transfer":
        sig = message.payload.get("signature", "")
        amount = message.payload.get("amount", 0)
        from_address = message.payload.get("from_address", "")

        verified = verify_transaction(wallet.rpc_client, sig)
        logger.info(f"Transaction {sig} verification: {verified}")

        app_state.add_transaction(
            direction="received",
            counterparty=from_address,
            amount=amount,
            signature=sig,
            status="confirmed" if verified else "failed",
        )

        return AgentMessage(
            type="confirm_receipt",
            sender=config.AGENT_ID,
            payload={"signature": sig, "confirmed": verified},
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    elif message.type == "confirm_receipt":
        return {"status": "ok"}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown message type: {message.type}")
