import { useCallback } from 'react';
import { AGENTS } from './api/agents';
import { useAgentStatus } from './hooks/useAgentStatus';
import { useTransactions } from './hooks/useTransactions';
import WalletCard from './components/WalletCard';
import TransferForm from './components/TransferForm';
import TransactionTable from './components/TransactionTable';

export default function App() {
  const agentA = useAgentStatus(AGENTS['agent-a'].url);
  const agentB = useAgentStatus(AGENTS['agent-b'].url);
  const { transactions } = useTransactions();

  const handleTransferComplete = useCallback(() => {
    // Force refresh both agents' status
    setTimeout(() => {
      agentA.refresh();
      agentB.refresh();
    }, 3000);
  }, [agentA, agentB]);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-3">
          Agent-to-Agent Solana Transfer
        </h1>
        <p className="text-center text-gray-400 mb-6 max-w-2xl mx-auto text-sm leading-relaxed">
          Two independent AI agents, each running in its own Docker container with no shared
          state, discover each other over a network, exchange wallet addresses, and execute
          real token transfers on the Solana blockchain. Every transfer is orchestrated
          autonomously by a Claude-powered LangChain agent that reasons through the steps:
          discover peer, verify balance, sign and submit the transaction, then confirm
          receipt on-chain. No hardcoded addresses. No shared memory. Just two AI agents
          transacting as independent peers on an open network.
        </p>
      </div>

      <div className="max-w-4xl mx-auto space-y-6">
        {/* Wallet Cards */}
        <div className="flex gap-6">
          <WalletCard
            label="Agent A"
            status={agentA.status}
            error={agentA.error}
            loading={agentA.loading}
          />
          <WalletCard
            label="Agent B"
            status={agentB.status}
            error={agentB.error}
            loading={agentB.loading}
          />
        </div>

        {/* Transfer Form */}
        <TransferForm onTransferComplete={handleTransferComplete} />

        {/* Transaction History */}
        <TransactionTable transactions={transactions} />
      </div>
    </div>
  );
}
