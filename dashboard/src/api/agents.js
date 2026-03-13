const AGENT_A_URL = import.meta.env.VITE_AGENT_A_URL || 'http://localhost:8001';
const AGENT_B_URL = import.meta.env.VITE_AGENT_B_URL || 'http://localhost:8002';

export const AGENTS = {
  'agent-a': { url: AGENT_A_URL, label: 'Agent A' },
  'agent-b': { url: AGENT_B_URL, label: 'Agent B' },
};

export async function fetchAgentStatus(agentUrl) {
  const resp = await fetch(`${agentUrl}/status`);
  if (!resp.ok) throw new Error(`Status fetch failed: ${resp.status}`);
  return resp.json();
}

export async function fetchTransactions(agentUrl) {
  const resp = await fetch(`${agentUrl}/transactions`);
  if (!resp.ok) throw new Error(`Transactions fetch failed: ${resp.status}`);
  return resp.json();
}

export async function triggerTransfer(agentUrl, toAgent, amount) {
  const resp = await fetch(`${agentUrl}/transfer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ to_agent: toAgent, amount }),
  });
  if (!resp.ok) {
    const error = await resp.json().catch(() => ({}));
    throw new Error(error.detail || `Transfer failed: ${resp.status}`);
  }
  return resp.json();
}
