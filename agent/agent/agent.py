import logging

from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

import config
from agent.tools.wallet import check_balance, transfer_sol, get_wallet_address
from agent.tools.messaging import request_peer_address, notify_peer_of_transfer
from state import app_state

logger = logging.getLogger(__name__)

TOOLS = [check_balance, transfer_sol, get_wallet_address, request_peer_address, notify_peer_of_transfer]


def create_agent() -> AgentExecutor:
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0,
        anthropic_api_key=config.ANTHROPIC_API_KEY,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a crypto wallet agent ({agent_id}). You can check your balance, "
         "transfer SOL on Solana devnet, and communicate with other agents. "
         "When asked to transfer SOL to another agent:\n"
         "1. First, request the peer agent's wallet address using request_peer_address\n"
         "2. Check your own balance to confirm you have enough\n"
         "3. Transfer the SOL to the peer's address using transfer_sol\n"
         "4. Notify the peer of the transfer using notify_peer_of_transfer\n"
         "Always verify addresses before transferring. Never invent addresses."
         ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=True, max_iterations=10)


async def run_transfer_agent(to_agent: str, amount: float):
    """Run the LangChain agent to perform a transfer."""
    logger.info(f"Starting agent transfer: {amount} SOL to {to_agent}")

    executor = create_agent()
    result = executor.invoke({
        "input": f"Transfer {amount} SOL to the peer agent ({to_agent}). "
                 f"Follow the steps: request their address, check your balance, "
                 f"transfer the SOL, then notify them.",
        "agent_id": config.AGENT_ID,
    })

    logger.info(f"Agent transfer result: {result.get('output', 'No output')}")

    # Parse the transfer result to log the transaction
    output = result.get("output", "")
    if isinstance(output, list):
        output = " ".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in output)
    output = str(output)
    if "confirmed" in output.lower():
        # Try to extract signature from the output
        import re
        sig_match = re.search(r"Signature: (\w+)", output)
        signature = sig_match.group(1) if sig_match else ""

        from wallet.manager import WalletManager
        wallet = WalletManager.get_instance()

        app_state.add_transaction(
            direction="sent",
            counterparty=to_agent,
            amount=amount,
            signature=signature,
            status="confirmed",
        )

    return result.get("output", "Transfer completed")
