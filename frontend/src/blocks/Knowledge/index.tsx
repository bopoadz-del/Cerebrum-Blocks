import { useState } from 'react';

interface KnowledgeBlockProps {
  apiKey: string;
}

export const KnowledgeBlock: React.FC<KnowledgeBlockProps> = ({ apiKey }) => {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'ask' | 'search'>('ask');

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const run = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const endpoint = mode === 'ask' ? '/knowledge/ask' : '/knowledge/search';
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          question: mode === 'ask' ? question : undefined,
          query: mode === 'search' ? question : undefined,
          top_k: 5,
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
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
        <button
          onClick={() => setMode('ask')}
          style={{
            flex: 1,
            padding: '6px',
            background: mode === 'ask' ? '#007bff' : '#e9ecef',
            color: mode === 'ask' ? 'white' : '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          ❓ Ask
        </button>
        <button
          onClick={() => setMode('search')}
          style={{
            flex: 1,
            padding: '6px',
            background: mode === 'search' ? '#007bff' : '#e9ecef',
            color: mode === 'search' ? 'white' : '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          🔍 Search
        </button>
      </div>
      <input
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder={mode === 'ask' ? 'Ask anything about your knowledge base...' : 'Search query...'}
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', marginBottom: '8px', boxSizing: 'border-box' }}
        onKeyDown={(e) => e.key === 'Enter' && run()}
      />
      <button
        onClick={run}
        disabled={loading || !question.trim()}
        style={{
          width: '100%',
          padding: '10px',
          background: loading || !question.trim() ? '#6c757d' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading || !question.trim() ? 'not-allowed' : 'pointer',
          fontWeight: 'bold',
        }}
      >
        {loading ? 'Thinking...' : mode === 'ask' ? '🧠 Ask Knowledge Base' : '🔍 Search'}
      </button>
      {result && (
        <div style={{ marginTop: '10px' }}>
          {result.answer && (
            <div style={{ padding: '10px', background: '#e3f2fd', borderRadius: '4px', fontSize: '13px', marginBottom: '8px', whiteSpace: 'pre-wrap' }}>
              {result.answer}
            </div>
          )}
          {result.confidence !== undefined && (
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
              Confidence: {(result.confidence * 100).toFixed(0)}% | Chunks: {result.chunks_retrieved || 0}
            </div>
          )}
          <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: '10px', borderRadius: '4px', fontSize: '11px', overflow: 'auto', maxHeight: '200px', margin: 0 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
