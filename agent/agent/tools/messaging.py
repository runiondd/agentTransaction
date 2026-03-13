import logging
from datetime import datetime

import httpx
from langchain_core.tools import tool

import config

logger = logging.getLogger(__name__)


@tool
def request_peer_address() -> str:
    """Request the peer agent's wallet address. Call this before transferring SOL."""
    peer_url = config.PEER_AGENT_URL
    logger.info(f"Requesting address from peer at {peer_url}")

    for attempt in range(3):
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{peer_url}/message",
                    json={
                        "type": "request_address",
                        "sender": config.AGENT_ID,
                        "payload": {},
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    },
                )
                resp.raise_for_status()
                msg = resp.json()
                wallet_address = msg["payload"]["wallet_address"]
                logger.info(f"Peer wallet address: {wallet_address}")
                return f"Peer wallet address: {wallet_address}"
        except httpx.ConnectError:
            logger.warning(f"Attempt {attempt + 1}: Peer unreachable at {peer_url}")
            if attempt < 2:
                import time
                time.sleep(2 ** attempt)
        except httpx.TimeoutException:
            logger.warning(f"Attempt {attempt + 1}: Peer request timed out")
            if attempt < 2:
                import time
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                import time
                time.sleep(2 ** attempt)

    return "Error: Failed to get peer address after 3 attempts. Peer may be unreachable."


@tool
def notify_peer_of_transfer(signature: str, amount: float, from_address: str) -> str:
    """Notify the peer agent that a transfer has been made.

    Args:
        signature: The Solana transaction signature
        amount: Amount of SOL transferred
        from_address: The sender's wallet address
    """
    peer_url = config.PEER_AGENT_URL
    logger.info(f"Notifying peer of transfer: {signature}")

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{peer_url}/message",
                json={
                    "type": "notify_transfer",
                    "sender": config.AGENT_ID,
                    "payload": {
                        "signature": signature,
                        "amount": amount,
                        "from_address": from_address,
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                },
            )
            resp.raise_for_status()
            msg = resp.json()
            confirmed = msg.get("payload", {}).get("confirmed", False)
            return f"Peer confirmation: {'confirmed' if confirmed else 'not confirmed'}"
    except httpx.ConnectError:
        logger.error(f"Peer unreachable at {peer_url} during transfer notification")
        return "Error: Peer agent is unreachable. Transfer completed on-chain but peer was not notified."
    except httpx.TimeoutException:
        logger.error(f"Peer notification timed out")
        return "Error: Peer notification timed out. Transfer completed on-chain but peer may not be aware."
    except Exception as e:
        logger.error(f"Failed to notify peer: {e}")
        return f"Error notifying peer: {e}"
