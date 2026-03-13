from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class StatusResponse(BaseModel):
    agent_id: str
    healthy: bool
    wallet_address: Optional[str] = None
    sol_balance: Optional[float] = None
    peer_agent_url: Optional[str] = None


class TransactionRecord(BaseModel):
    id: str
    timestamp: str
    direction: str  # "sent" or "received"
    counterparty: str
    amount: float
    signature: str
    status: str  # "pending", "confirmed", "failed"
    explorer_url: str


class TransactionsResponse(BaseModel):
    transactions: List[TransactionRecord]


class TransferRequest(BaseModel):
    to_agent: str
    amount: float


class TransferResponse(BaseModel):
    transfer_id: str
    status: str


class AgentMessage(BaseModel):
    type: str  # request_address, share_address, notify_transfer, confirm_receipt
    sender: str
    payload: Dict[str, Any] = {}
    timestamp: Optional[str] = None
