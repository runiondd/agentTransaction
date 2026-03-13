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
      <h1 className="text-3xl font-bold text-center mb-8">
        Agent-to-Agent Solana Transfer Dashboard
      </h1>

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
