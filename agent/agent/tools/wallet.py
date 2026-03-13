import logging

from langchain_core.tools import tool

from wallet.manager import WalletManager
from wallet.transfer import transfer_sol as do_transfer

logger = logging.getLogger(__name__)


@tool
def check_balance() -> str:
    """Check the current SOL balance of this agent's wallet."""
    manager = WalletManager.get_instance()
    balance = manager.get_balance()
    return f"Current balance: {balance} SOL (address: {manager.address})"


@tool
def get_wallet_address() -> str:
    """Get this agent's Solana wallet address."""
    manager = WalletManager.get_instance()
    return f"My wallet address is: {manager.address}"


@tool
def transfer_sol(recipient_address: str, amount: float) -> str:
    """Transfer SOL to a recipient wallet address on Solana devnet.

    Args:
        recipient_address: Base58-encoded Solana wallet address of the recipient
        amount: Amount of SOL to transfer (must be positive)
    """
    if amount <= 0:
        return "Error: Amount must be positive"
    if len(recipient_address) < 32:
        return "Error: Invalid wallet address"

    manager = WalletManager.get_instance()
    try:
        result = do_transfer(
            manager.rpc_client, manager.keypair, recipient_address, amount
        )
        return (
            f"Transfer {result.status}: {result.amount} SOL to {recipient_address}. "
            f"Signature: {result.signature}. Explorer: {result.explorer_url}"
        )
    except ValueError as e:
        logger.warning(f"Transfer validation error: {e}")
        return f"Error: {e}"
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        return f"Transfer failed: {e}"
