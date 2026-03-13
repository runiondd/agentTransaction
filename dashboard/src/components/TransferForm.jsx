import { useState } from 'react';
import { triggerTransfer, AGENTS } from '../api/agents';

export default function TransferForm({ onTransferComplete }) {
  const [direction, setDirection] = useState('a-to-b');
  const [amount, setAmount] = useState('');
  const [status, setStatus] = useState('idle'); // idle, sending, success, error
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const amountNum = parseFloat(amount);
    if (!amountNum || amountNum <= 0) {
      setStatus('error');
      setMessage('Enter a positive amount');
      return;
    }

    setStatus('sending');
    setMessage('');

    const senderUrl = direction === 'a-to-b' ? AGENTS['agent-a'].url : AGENTS['agent-b'].url;
    const toAgent = direction === 'a-to-b' ? 'agent-b' : 'agent-a';

    try {
      const result = await triggerTransfer(senderUrl, toAgent, amountNum);
      setStatus('success');
      setMessage(`Transfer initiated! ID: ${result.transfer_id}`);
      setAmount('');
      if (onTransferComplete) onTransferComplete();
    } catch (err) {
      setStatus('error');
      setMessage(err.message);
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Transfer SOL</h2>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex gap-4">
          <select
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
            className="bg-gray-700 text-white rounded-lg px-4 py-2 flex-1"
            disabled={status === 'sending'}
          >
            <option value="a-to-b">Agent A &rarr; Agent B</option>
            <option value="b-to-a">Agent B &rarr; Agent A</option>
          </select>

          <input
            type="number"
            step="0.001"
            min="0"
            placeholder="Amount (SOL)"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="bg-gray-700 text-white rounded-lg px-4 py-2 flex-1"
            disabled={status === 'sending'}
          />

          <button
            type="submit"
            disabled={status === 'sending'}
            className={`px-6 py-2 rounded-lg font-semibold transition ${
              status === 'sending'
                ? 'bg-gray-600 text-gray-400 cursor-wait'
                : 'bg-blue-600 text-white hover:bg-blue-500'
            }`}
          >
            {status === 'sending' ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Sending...
              </span>
            ) : 'Send'}
          </button>
        </div>

        {message && (
          <p className={`text-sm ${status === 'error' ? 'text-red-400' : 'text-green-400'}`}>
            {message}
          </p>
        )}
      </form>
    </div>
  );
}
