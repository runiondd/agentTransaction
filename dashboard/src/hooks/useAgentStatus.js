import { useState, useEffect, useCallback } from 'react';
import { fetchAgentStatus } from '../api/agents';

export function useAgentStatus(agentUrl, intervalMs = 5000) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchAgentStatus(agentUrl);
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [agentUrl]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, intervalMs);
    return () => clearInterval(interval);
  }, [refresh, intervalMs]);

  return { status, error, loading, refresh };
}
