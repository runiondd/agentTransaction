"""
End-to-end smoke test for the agent-to-agent Solana transfer system.

Prerequisites:
  - Both agent containers running (docker compose up -d)
  - Both agents funded with SOL on devnet

Run:
  python -m pytest agent/tests/test_e2e.py -v --timeout=120
  OR standalone:
  python agent/tests/test_e2e.py
"""

import time
import requests

AGENT_A_URL = "http://localhost:8001"
AGENT_B_URL = "http://localhost:8002"
TRANSFER_AMOUNT = 0.01


def test_agent_a_status():
    """Agent A returns valid status with wallet info."""
    resp = requests.get(f"{AGENT_A_URL}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == "agent-a"
    assert data["healthy"] is True
    assert data["wallet_address"] is not None
    assert len(data["wallet_address"]) > 30
    assert data["sol_balance"] is not None
    assert data["sol_balance"] >= 0


def test_agent_b_status():
    """Agent B returns valid status with wallet info."""
    resp = requests.get(f"{AGENT_B_URL}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == "agent-b"
    assert data["healthy"] is True
    assert data["wallet_address"] is not None


def test_transactions_endpoint():
    """Both agents return transaction lists."""
    for url in [AGENT_A_URL, AGENT_B_URL]:
        resp = requests.get(f"{url}/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data
        assert isinstance(data["transactions"], list)


def test_message_request_address():
    """Agent responds to request_address with its wallet address."""
    resp = requests.post(
        f"{AGENT_A_URL}/message",
        json={
            "type": "request_address",
            "sender": "test",
            "payload": {},
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "share_address"
    assert "wallet_address" in data["payload"]
    assert len(data["payload"]["wallet_address"]) > 30


def test_message_invalid_type():
    """Agent returns 400 for unknown message type."""
    resp = requests.post(
        f"{AGENT_A_URL}/message",
        json={
            "type": "invalid_type",
            "sender": "test",
            "payload": {},
            "timestamp": "2026-01-01T00:00:00Z",
        },
    )
    assert resp.status_code == 400


def test_transfer_invalid_amount():
    """Agent rejects transfer with non-positive amount."""
    resp = requests.post(
        f"{AGENT_A_URL}/transfer",
        json={"to_agent": "agent-b", "amount": 0},
    )
    assert resp.status_code == 400


def test_transfer_a_to_b():
    """Full end-to-end transfer: Agent A sends SOL to Agent B via LangChain agent."""
    # Get starting balances
    a_before = requests.get(f"{AGENT_A_URL}/status").json()["sol_balance"]
    b_before = requests.get(f"{AGENT_B_URL}/status").json()["sol_balance"]

    assert a_before >= TRANSFER_AMOUNT + 0.001, (
        f"Agent A needs at least {TRANSFER_AMOUNT + 0.001} SOL, has {a_before}"
    )

    # Initiate transfer
    resp = requests.post(
        f"{AGENT_A_URL}/transfer",
        json={"to_agent": "agent-b", "amount": TRANSFER_AMOUNT},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "initiated"
    assert "transfer_id" in data

    # Wait for transfer to complete (LangChain agent + Solana confirmation)
    max_wait = 90
    poll_interval = 5
    elapsed = 0
    transfer_confirmed = False

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        a_after = requests.get(f"{AGENT_A_URL}/status").json()["sol_balance"]
        b_after = requests.get(f"{AGENT_B_URL}/status").json()["sol_balance"]

        # Check if balances changed
        if a_after < a_before and b_after > b_before:
            transfer_confirmed = True
            break

    assert transfer_confirmed, (
        f"Transfer not confirmed after {max_wait}s. "
        f"A: {a_before} -> {a_after}, B: {b_before} -> {b_after}"
    )

    # Verify balance changes are correct
    a_after = requests.get(f"{AGENT_A_URL}/status").json()["sol_balance"]
    b_after = requests.get(f"{AGENT_B_URL}/status").json()["sol_balance"]

    a_diff = a_before - a_after
    b_diff = b_after - b_before

    # Agent A should have lost transfer amount + small tx fee
    assert a_diff > TRANSFER_AMOUNT - 0.0001, f"Agent A balance drop too small: {a_diff}"
    assert a_diff < TRANSFER_AMOUNT + 0.01, f"Agent A balance drop too large: {a_diff}"

    # Agent B should have gained exactly the transfer amount
    assert abs(b_diff - TRANSFER_AMOUNT) < 0.0001, (
        f"Agent B balance gain incorrect: expected {TRANSFER_AMOUNT}, got {b_diff}"
    )

    # Check transaction appears in Agent B's log
    b_txs = requests.get(f"{AGENT_B_URL}/transactions").json()["transactions"]
    received = [tx for tx in b_txs if tx["direction"] == "received"]
    assert len(received) > 0, "Agent B has no received transactions"

    latest = received[-1]
    assert latest["status"] == "confirmed"
    assert latest["amount"] == TRANSFER_AMOUNT
    assert latest["signature"] != ""
    assert "explorer.solana.com" in latest["explorer_url"]


def test_transfer_b_to_a():
    """Reverse direction: Agent B sends SOL to Agent A."""
    b_before = requests.get(f"{AGENT_B_URL}/status").json()["sol_balance"]
    a_before = requests.get(f"{AGENT_A_URL}/status").json()["sol_balance"]

    assert b_before >= TRANSFER_AMOUNT + 0.001, (
        f"Agent B needs at least {TRANSFER_AMOUNT + 0.001} SOL, has {b_before}"
    )

    resp = requests.post(
        f"{AGENT_B_URL}/transfer",
        json={"to_agent": "agent-a", "amount": TRANSFER_AMOUNT},
    )
    assert resp.status_code == 202

    max_wait = 90
    poll_interval = 5
    elapsed = 0
    transfer_confirmed = False

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        b_after = requests.get(f"{AGENT_B_URL}/status").json()["sol_balance"]
        a_after = requests.get(f"{AGENT_A_URL}/status").json()["sol_balance"]

        if b_after < b_before and a_after > a_before:
            transfer_confirmed = True
            break

    assert transfer_confirmed, (
        f"Reverse transfer not confirmed after {max_wait}s. "
        f"B: {b_before} -> {b_after}, A: {a_before} -> {a_after}"
    )


if __name__ == "__main__":
    tests = [
        test_agent_a_status,
        test_agent_b_status,
        test_transactions_endpoint,
        test_message_request_address,
        test_message_invalid_type,
        test_transfer_invalid_amount,
        test_transfer_a_to_b,
        test_transfer_b_to_a,
    ]

    passed = 0
    failed = 0

    for test in tests:
        name = test.__name__
        try:
            print(f"  {name}...", end=" ", flush=True)
            test()
            print("PASSED")
            passed += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
