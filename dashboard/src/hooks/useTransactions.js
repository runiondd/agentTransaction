import { useState, useEffect } from 'react';
import { fetchTransactions, AGENTS } from '../api/agents';

export function useTransactions(intervalMs = 5000) {
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const results = await Promise.all(
          Object.entries(AGENTS).map(async ([id, agent]) => {
            try {
              const data = await fetchTransactions(agent.url);
              return data.transactions.map((tx) => ({ ...tx, agent_id: id }));
            } catch {
              return [];
            }
          })
        );

        // Flatten and deduplicate by signature
        const all = results.flat();
        const seen = new Set();
        const deduped = all.filter((tx) => {
          if (!tx.signature || seen.has(tx.signature)) return false;
          seen.add(tx.signature);
          return true;
        });

        deduped.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
        setTransactions(deduped);
        setError(null);
      } catch (err) {
        setError(err.message);
      }
    };

    poll();
    const interval = setInterval(poll, intervalMs);
    return () => clearInterval(interval);
  }, [intervalMs]);

  return { transactions, error };
}
