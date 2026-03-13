import uuid
from datetime import datetime
from typing import List, Optional

from models.schemas import TransactionRecord


class AppState:
    def __init__(self):
        self.transactions: List[TransactionRecord] = []
        self.peer_address: Optional[str] = None

    def add_transaction(
        self,
        direction: str,
        counterparty: str,
        amount: float,
        signature: str,
        status: str,
    ) -> TransactionRecord:
        explorer_url = (
            f"https://explorer.solana.com/tx/{signature}?cluster=devnet"
            if signature
            else ""
        )
        record = TransactionRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            direction=direction,
            counterparty=counterparty,
            amount=amount,
            signature=signature,
            status=status,
            explorer_url=explorer_url,
        )
        self.transactions.append(record)
        return record

    def get_transactions(self) -> List[TransactionRecord]:
        return sorted(self.transactions, key=lambda t: t.timestamp, reverse=True)


app_state = AppState()
