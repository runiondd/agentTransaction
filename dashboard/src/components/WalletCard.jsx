import { useState } from 'react';

function truncateAddress(addr) {
  if (!addr || addr.length < 8) return addr || '...';
  return `${addr.slice(0, 4)}...${addr.slice(-4)}`;
}

export default function WalletCard({ label, status, error, loading }) {
  const [copied, setCopied] = useState(false);

  const copyAddress = () => {
    if (status?.wallet_address) {
      navigator.clipboard.writeText(status.wallet_address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 flex-1 animate-pulse">
        <h2 className="text-xl font-semibold text-gray-400">{label}</h2>
        <div className="h-8 bg-gray-700 rounded mt-4 w-32"></div>
        <div className="h-6 bg-gray-700 rounded mt-2 w-48"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 flex-1 border border-red-500/30">
        <h2 className="text-xl font-semibold text-red-400">{label}</h2>
        <p className="text-red-300 mt-2 text-sm">Offline: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6 flex-1">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">{label}</h2>
        <span className="inline-block w-2 h-2 rounded-full bg-green-400"></span>
      </div>

      <div className="mt-4">
        <p className="text-3xl font-bold text-white">
          {status?.sol_balance != null ? `${status.sol_balance.toFixed(4)} SOL` : '-- SOL'}
        </p>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <code className="text-sm text-gray-400">
          {truncateAddress(status?.wallet_address)}
        </code>
        <button
          onClick={copyAddress}
          className="text-xs text-blue-400 hover:text-blue-300 transition"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
    </div>
  );
}
