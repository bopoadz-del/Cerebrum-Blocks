import { useState } from 'react';

interface AgentSwarmBlockProps {
  apiKey: string;
}

export const AgentSwarmBlock: React.FC<AgentSwarmBlockProps> = ({ apiKey }) => {
  const [objective, setObjective] = useState('Write a FastAPI auth endpoint');
  const [agentsJson, setAgentsJson] = useState(
    JSON.stringify(
      [
        { name: 'architect', role: 'planner', goal: 'Design API structure', backstory: 'Senior backend architect' },
        { name: 'coder', role: 'coder', goal: 'Implement the code', backstory: 'Python specialist' },
      ],
      null,
      2
    )
  );
  const [tasksJson, setTasksJson] = useState(
    JSON.stringify(
      [
        { id: 'design', description: 'Design Pydantic models', agent: 'architect', expected_output: 'Schema' },
        { id: 'implement', description: 'Write FastAPI code', agent: 'coder', expected_output: 'Python file', dependencies: ['design'] },
      ],
      null,
      2
    )
  );
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const runSwarm = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/swarm/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          project_id: 'web-ui',
          objective,
          agents: JSON.parse(agentsJson),
          tasks: JSON.parse(tasksJson),
        }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setResult({ error: String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '15px' }}>
      <input
        type="text"
        value={objective}
        onChange={(e) => setObjective(e.target.value)}
        placeholder="Objective"
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', marginBottom: '8px', boxSizing: 'border-box' }}
      />
      <textarea
        value={agentsJson}
        onChange={(e) => setAgentsJson(e.target.value)}
        rows={4}
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', fontFamily: 'monospace', fontSize: '11px', marginBottom: '8px', boxSizing: 'border-box' }}
      />
      <textarea
        value={tasksJson}
        onChange={(e) => setTasksJson(e.target.value)}
        rows={4}
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', fontFamily: 'monospace', fontSize: '11px', marginBottom: '8px', boxSizing: 'border-box' }}
      />
      <button
        onClick={runSwarm}
        disabled={loading}
        style={{
          width: '100%',
          padding: '10px',
          background: loading ? '#6c757d' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
          fontWeight: 'bold',
        }}
      >
        {loading ? 'Running Swarm...' : '🐝 Run Agent Swarm'}
      </button>
      {result && (
        <div style={{ marginTop: '10px' }}>
          {result.swarm_id && (
            <div style={{ fontSize: '12px', color: '#28a745', marginBottom: '5px' }}>
              ✅ Swarm: <code>{result.swarm_id}</code> | Tokens: {result.total_tokens} | Time: {result.total_time_ms}ms
            </div>
          )}
          <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: '10px', borderRadius: '4px', fontSize: '11px', overflow: 'auto', maxHeight: '250px', margin: 0 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
