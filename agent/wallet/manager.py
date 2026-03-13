import json
import logging
import os
import time
from typing import Optional

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed

import config

logger = logging.getLogger(__name__)


class WalletManager:
    _instance: Optional["WalletManager"] = None

    def __init__(self):
        self.rpc_client = Client(config.SOLANA_RPC_URL)
        self.keypair: Optional[Keypair] = None
        self._address: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "WalletManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def address(self) -> str:
        if self._address is None:
            raise RuntimeError("Wallet not initialized. Call init_wallet() first.")
        return self._address

    def init_wallet(self) -> str:
        """Generate or load a Solana keypair. Returns the wallet address."""
        wallet_path = config.WALLET_PATH

        if os.path.exists(wallet_path):
            logger.info(f"Loading existing keypair from {wallet_path}")
            with open(wallet_path, "r") as f:
                secret_bytes = json.load(f)
            self.keypair = Keypair.from_bytes(bytes(secret_bytes))
        else:
            logger.info("No existing keypair found. Generating new one.")
            self.keypair = Keypair()
            os.makedirs(os.path.dirname(wallet_path), exist_ok=True)
            with open(wallet_path, "w") as f:
                json.dump(list(bytes(self.keypair)), f)
            logger.info(f"Keypair saved to {wallet_path}")

        self._address = str(self.keypair.pubkey())
        logger.info(f"Wallet address: {self._address}")
        return self._address

    def get_balance(self) -> float:
        """Get current SOL balance with retry logic."""
        for attempt in range(3):
            try:
                resp = self.rpc_client.get_balance(
                    self.keypair.pubkey(), commitment=Confirmed
                )
                lamports = resp.value
                return lamports / 1_000_000_000
            except Exception as e:
                logger.warning(f"Balance query attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
        raise RuntimeError("Failed to query balance after 3 attempts")

    def request_airdrop(self, amount_sol: float = 2.0) -> bool:
        """Request devnet SOL airdrop. Returns True on success."""
        lamports = int(amount_sol * 1_000_000_000)
        logger.info(f"Requesting airdrop of {amount_sol} SOL...")

        for attempt in range(3):
            try:
                resp = self.rpc_client.request_airdrop(
                    self.keypair.pubkey(), lamports, commitment=Confirmed
                )
                sig = resp.value
                logger.info(f"Airdrop requested. Signature: {sig}")
                # Wait for confirmation
                self._confirm_transaction(str(sig))
                balance = self.get_balance()
                logger.info(f"Airdrop confirmed. New balance: {balance} SOL")
                return True
            except Exception as e:
                logger.warning(f"Airdrop attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)

        logger.error("Failed to airdrop after 3 attempts")
        return False

    def _confirm_transaction(self, signature: str, timeout: int = 30):
        """Wait for transaction confirmation."""
        from solders.signature import Signature

        sig = Signature.from_string(signature)
        start = time.time()
        while time.time() - start < timeout:
            resp = self.rpc_client.get_signature_statuses([sig])
            statuses = resp.value
            if statuses and statuses[0] is not None:
                if statuses[0].confirmation_status is not None:
                    return
            time.sleep(1)
        logger.warning(f"Transaction {signature} not confirmed within {timeout}s")
