function truncateSig(sig) {
  if (!sig || sig.length < 12) return sig || '--';
  return `${sig.slice(0, 6)}...${sig.slice(-4)}`;
}

export default function TransactionTable({ transactions }) {
  if (!transactions || transactions.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Transaction History</h2>
        <p className="text-gray-400 text-sm">No transactions yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Transaction History</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-gray-400 border-b border-gray-700">
            <tr>
              <th className="py-2 px-3">Time</th>
              <th className="py-2 px-3">Direction</th>
              <th className="py-2 px-3">Amount</th>
              <th className="py-2 px-3">Signature</th>
              <th className="py-2 px-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id} className="border-b border-gray-700/50 text-gray-300">
                <td className="py-2 px-3 whitespace-nowrap">
                  {new Date(tx.timestamp).toLocaleString()}
                </td>
                <td className="py-2 px-3">
                  <span className={tx.direction === 'sent' ? 'text-red-400' : 'text-green-400'}>
                    {tx.direction === 'sent' ? 'Sent' : 'Received'}
                  </span>
                </td>
                <td className="py-2 px-3 font-mono">{tx.amount} SOL</td>
                <td className="py-2 px-3">
                  {tx.explorer_url ? (
                    <a
                      href={tx.explorer_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 font-mono"
                    >
                      {truncateSig(tx.signature)}
                    </a>
                  ) : (
                    <span className="font-mono">{truncateSig(tx.signature)}</span>
                  )}
                </td>
                <td className="py-2 px-3">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                      tx.status === 'confirmed'
                        ? 'bg-green-900/50 text-green-400'
                        : tx.status === 'failed'
                        ? 'bg-red-900/50 text-red-400'
                        : 'bg-yellow-900/50 text-yellow-400'
                    }`}
                  >
                    {tx.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
