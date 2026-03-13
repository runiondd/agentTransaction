import logging
import time
from dataclasses import dataclass

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.signature import Signature
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed

logger = logging.getLogger(__name__)


@dataclass
class TransferResult:
    signature: str
    status: str  # "confirmed" or "failed"
    amount: float
    recipient: str
    explorer_url: str


def validate_address(address: str) -> bool:
    """Validate a Base58 Solana address."""
    try:
        pubkey = Pubkey.from_string(address)
        return len(bytes(pubkey)) == 32
    except Exception:
        return False


def transfer_sol(
    rpc_client: Client,
    sender_keypair: Keypair,
    recipient_address: str,
    amount_sol: float,
) -> TransferResult:
    """Construct, sign, and submit a SOL transfer transaction."""
    if amount_sol <= 0:
        raise ValueError("Transfer amount must be positive")

    if not validate_address(recipient_address):
        raise ValueError(f"Invalid recipient address: {recipient_address}")

    recipient_pubkey = Pubkey.from_string(recipient_address)
    lamports = int(amount_sol * 1_000_000_000)

    # Check balance
    balance_resp = rpc_client.get_balance(sender_keypair.pubkey(), commitment=Confirmed)
    balance_lamports = balance_resp.value
    if balance_lamports < lamports + 5000:  # 5000 lamports for tx fee
        raise ValueError(
            f"Insufficient balance: have {balance_lamports / 1e9} SOL, "
            f"need {amount_sol} SOL + fee"
        )

    logger.info(
        f"Transferring {amount_sol} SOL from {sender_keypair.pubkey()} "
        f"to {recipient_address}"
    )

    for attempt in range(3):
        try:
            # Get recent blockhash (use Finalized to avoid stale blockhash errors)
            blockhash_resp = rpc_client.get_latest_blockhash()
            recent_blockhash = blockhash_resp.value.blockhash

            # Build transaction
            ix = transfer(
                TransferParams(
                    from_pubkey=sender_keypair.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports,
                )
            )
            tx = Transaction.new_signed_with_payer(
                [ix],
                sender_keypair.pubkey(),
                [sender_keypair],
                recent_blockhash,
            )

            # Submit
            send_resp = rpc_client.send_transaction(tx)
            sig_str = str(send_resp.value)
            logger.info(f"Transaction submitted. Signature: {sig_str}")

            # Wait for confirmation
            _wait_for_confirmation(rpc_client, sig_str)

            explorer_url = (
                f"https://explorer.solana.com/tx/{sig_str}?cluster=devnet"
            )
            logger.info(f"Transfer confirmed: {explorer_url}")

            return TransferResult(
                signature=sig_str,
                status="confirmed",
                amount=amount_sol,
                recipient=recipient_address,
                explorer_url=explorer_url,
            )

        except ValueError:
            raise
        except Exception as e:
            logger.warning(f"Transfer attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)

    return TransferResult(
        signature="",
        status="failed",
        amount=amount_sol,
        recipient=recipient_address,
        explorer_url="",
    )


def _wait_for_confirmation(rpc_client: Client, signature: str, timeout: int = 30):
    """Wait for a transaction to be confirmed."""
    sig = Signature.from_string(signature)
    start = time.time()
    while time.time() - start < timeout:
        resp = rpc_client.get_signature_statuses([sig])
        statuses = resp.value
        if statuses and statuses[0] is not None:
            if statuses[0].confirmation_status is not None:
                return
        time.sleep(1)
    logger.warning(f"Transaction {signature} not confirmed within {timeout}s")


def verify_transaction(rpc_client: Client, signature: str) -> bool:
    """Verify a transaction exists and is confirmed on-chain."""
    try:
        sig = Signature.from_string(signature)
        resp = rpc_client.get_signature_statuses([sig])
        statuses = resp.value
        if statuses and statuses[0] is not None:
            return statuses[0].err is None
        return False
    except Exception as e:
        logger.error(f"Failed to verify transaction {signature}: {e}")
        return False
