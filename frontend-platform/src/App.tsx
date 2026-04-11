import { useState, useEffect } from 'react';
import { 
  Terminal, Key, Book, Activity, Box, Layers, 
  Send, Play, ChevronRight, Server, Shield 
} from 'lucide-react';

interface BlockTestResult {
  block: string;
  status: 'success' | 'error';
  result: any;
  duration: number;
}

const API_BASE = 'https://ssdppg.onrender.com';

const BLOCKS = [
  { name: 'chat', display: 'Chat AI', description: 'Multi-provider LLM' },
  { name: 'pdf', display: 'PDF', description: 'PDF text extraction' },
  { name: 'ocr', display: 'OCR', description: 'Image text extraction' },
  { name: 'construction', display: 'Construction', description: 'AEC domain AI' },
  { name: 'medical', display: 'Medical', description: 'Healthcare AI' },
  { name: 'legal', display: 'Legal', description: 'Legal document AI' },
  { name: 'finance', display: 'Finance', description: 'Risk & compliance AI' },
  { name: 'security', display: 'Security', description: 'Auth & sandbox' },
  { name: 'ai_core', display: 'AI Core', description: 'Routing & failover' },
  { name: 'store', display: 'Store', description: 'Marketplace' },
];

function App() {
  const [activeTab, setActiveTab] = useState<'playground' | 'api' | 'keys' | 'health'>('playground');
  const [selectedBlock, setSelectedBlock] = useState('chat');
  const [input, setInput] = useState('');
  const [params, setParams] = useState('{}');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [apiKey, setApiKey] = useState('');
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    fetchHealth();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data = await res.json();
      setHealth(data);
    } catch (e) {
      setHealth({ status: 'error' });
    }
  };

  const executeBlock = async () => {
    setLoading(true);
    setResult(null);
    
    try {
      const body: any = {
        block: selectedBlock,
        input: input || {},
        params: JSON.parse(params || '{}')
      };
      
      const headers: any = { 'Content-Type': 'application/json' };
      if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;
      
      const start = Date.now();
      const res = await fetch(`${API_BASE}/execute`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
      });
      
      const data = await res.json();
      setResult({
        ...data,
        _duration: Date.now() - start
      });
    } catch (e: any) {
      setResult({ status: 'error', error: e.message });
    } finally {
      setLoading(false);
    }
  };

  const generateKey = async () => {
    try {
      const res = await fetch(`${API_BASE}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          block: 'security',
          input: {},
          params: { action: 'create_key', owner: 'platform_user' }
        })
      });
      const data = await res.json();
      if (data.result?.api_key) {
        setApiKey(data.result.api_key);
      }
    } catch (e) {
      alert('Failed to generate key');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0f', display: 'flex' }}>
      {/* Sidebar */}
      <aside style={{ 
        width: '240px', 
        background: '#1a1a2e', 
        borderRight: '1px solid #2a2a3e',
        padding: '20px 0'
      }}>
        <div style={{ padding: '0 20px 20px', borderBottom: '1px solid #2a2a3e' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '24px' }}>🧠</span>
            <div>
              <h1 style={{ margin: 0, fontSize: '16px', color: '#fff' }}>Platform</h1>
              <p style={{ margin: 0, fontSize: '11px', color: '#666' }}>Developer Console</p>
            </div>
          </div>
        </div>

        <nav style={{ padding: '20px 0' }}>
          {[
            { id: 'playground', icon: Terminal, label: 'Playground' },
            { id: 'api', icon: Book, label: 'API Docs' },
            { id: 'keys', icon: Key, label: 'API Keys' },
            { id: 'health', icon: Activity, label: 'Health' },
          ].map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id as any)}
              style={{
                width: '100%',
                padding: '12px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                background: activeTab === item.id ? '#6c63ff22' : 'transparent',
                border: 'none',
                borderLeft: activeTab === item.id ? '3px solid #6c63ff' : '3px solid transparent',
                color: activeTab === item.id ? '#fff' : '#888',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              <item.icon size={18} />
              {item.label}
            </button>
          ))}
        </nav>

        <div style={{ padding: '20px', borderTop: '1px solid #2a2a3e', marginTop: 'auto' }}>
          <a 
            href="https://cerebrum-store.onrender.com" 
            target="_blank"
            rel="noopener noreferrer"
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              color: '#6c63ff',
              textDecoration: 'none',
              fontSize: '13px'
            }}
          >
            <Box size={16} />
            Block Store →
          </a>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '30px', overflow: 'auto' }}>
        {/* Header */}
        <header style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '30px'
        }}>
          <h2 style={{ margin: 0, color: '#fff', fontSize: '24px' }}>
            {activeTab === 'playground' && 'Block Playground'}
            {activeTab === 'api' && 'API Documentation'}
            {activeTab === 'keys' && 'API Key Management'}
            {activeTab === 'health' && 'System Health'}
          </h2>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ 
              padding: '6px 12px', 
              background: health?.status === 'healthy' ? '#00c85322' : '#ff444422',
              borderRadius: '6px',
              fontSize: '12px',
              color: health?.status === 'healthy' ? '#00c853' : '#ff4444'
            }}>
              API: {health?.status || 'unknown'}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {health?.blocks_available || 0} blocks
            </div>
          </div>
        </header>

        {/* Playground Tab */}
        {activeTab === 'playground' && (
          <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px' }}>
            {/* Block Selector */}
            <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '20px' }}>
              <h3 style={{ margin: '0 0 16px', color: '#fff', fontSize: '14px' }}>Select Block</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {BLOCKS.map(block => (
                  <button
                    key={block.name}
                    onClick={() => setSelectedBlock(block.name)}
                    style={{
                      padding: '12px',
                      textAlign: 'left',
                      background: selectedBlock === block.name ? '#6c63ff' : '#0a0a0f',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#fff',
                      cursor: 'pointer',
                      fontSize: '13px'
                    }}
                  >
                    <div style={{ fontWeight: 'bold' }}>{block.display}</div>
                    <div style={{ fontSize: '11px', opacity: 0.7 }}>{block.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Test Panel */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '20px' }}>
                <h3 style={{ margin: '0 0 16px', color: '#fff', fontSize: '14px' }}>Test {selectedBlock}</h3>
                
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', color: '#888', fontSize: '12px' }}>Input</label>
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Enter input data..."
                    style={{
                      width: '100%',
                      height: '80px',
                      padding: '12px',
                      background: '#0a0a0f',
                      border: '1px solid #2a2a3e',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '13px',
                      fontFamily: 'monospace'
                    }}
                  />
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', color: '#888', fontSize: '12px' }}>Params (JSON)</label>
                  <textarea
                    value={params}
                    onChange={(e) => setParams(e.target.value)}
                    style={{
                      width: '100%',
                      height: '60px',
                      padding: '12px',
                      background: '#0a0a0f',
                      border: '1px solid #2a2a3e',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '13px',
                      fontFamily: 'monospace'
                    }}
                  />
                </div>

                <button
                  onClick={executeBlock}
                  disabled={loading}
                  style={{
                    padding: '12px 24px',
                    background: '#6c63ff',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                    fontWeight: 'bold',
                    cursor: loading ? 'wait' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <Play size={16} />
                  {loading ? 'Executing...' : 'Execute Block'}
                </button>
              </div>

              {/* Result */}
              {result && (
                <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <h3 style={{ margin: 0, color: '#fff', fontSize: '14px' }}>Result</h3>
                    <span style={{ 
                      padding: '4px 8px', 
                      borderRadius: '4px',
                      fontSize: '11px',
                      background: result.status === 'success' ? '#00c85322' : '#ff444422',
                      color: result.status === 'success' ? '#00c853' : '#ff4444'
                    }}>
                      {result.status}
                    </span>
                  </div>
                  <pre style={{ 
                    background: '#0a0a0f',
                    padding: '16px',
                    borderRadius: '8px',
                    overflow: 'auto',
                    fontSize: '12px',
                    color: '#aaa',
                    maxHeight: '300px'
                  }}>
                    {JSON.stringify(result, null, 2)}
                  </pre>
                  {result._duration && (
                    <div style={{ marginTop: '8px', fontSize: '11px', color: '#666' }}>
                      Duration: {result._duration}ms
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* API Docs Tab */}
        {activeTab === 'api' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '24px' }}>
              <h3 style={{ margin: '0 0 16px', color: '#fff' }}>Base URL</h3>
              <code style={{ 
                background: '#0a0a0f',
                padding: '12px 16px',
                borderRadius: '6px',
                display: 'block',
                fontFamily: 'monospace',
                color: '#6c63ff'
              }}>
                {API_BASE}
              </code>
            </div>

            {[
              { method: 'GET', path: '/health', desc: 'Health check' },
              { method: 'GET', path: '/blocks', desc: 'List all blocks' },
              { method: 'POST', path: '/execute', desc: 'Execute a block', body: '{"block": "chat", "input": "...", "params": {}}' },
              { method: 'POST', path: '/chain', desc: 'Execute a chain', body: '{"steps": [...], "initial_input": {}}' },
            ].map(endpoint => (
              <div key={endpoint.path} style={{ background: '#1a1a2e', borderRadius: '12px', padding: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <span style={{ 
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    background: endpoint.method === 'GET' ? '#00c85322' : '#ff6b3522',
                    color: endpoint.method === 'GET' ? '#00c853' : '#ff6b35'
                  }}>
                    {endpoint.method}
                  </span>
                  <code style={{ color: '#fff', fontFamily: 'monospace' }}>{endpoint.path}</code>
                </div>
                <p style={{ margin: '0 0 8px', color: '#888', fontSize: '13px' }}>{endpoint.desc}</p>
                {endpoint.body && (
                  <pre style={{ 
                    background: '#0a0a0f',
                    padding: '12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: '#aaa',
                    overflow: 'auto'
                  }}>
                    {endpoint.body}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Keys Tab */}
        {activeTab === 'keys' && (
          <div style={{ maxWidth: '600px' }}>
            <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '24px', marginBottom: '20px' }}>
              <h3 style={{ margin: '0 0 16px', color: '#fff' }}>Your API Key</h3>
              
              <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                <input
                  type="text"
                  value={apiKey}
                  readOnly
                  placeholder="No API key generated"
                  style={{
                    flex: 1,
                    padding: '12px',
                    background: '#0a0a0f',
                    border: '1px solid #2a2a3e',
                    borderRadius: '8px',
                    color: apiKey ? '#fff' : '#666',
                    fontFamily: 'monospace'
                  }}
                />
                <button
                  onClick={generateKey}
                  style={{
                    padding: '12px 20px',
                    background: '#6c63ff',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                    fontWeight: 'bold',
                    cursor: 'pointer'
                  }}
                >
                  Generate
                </button>
              </div>

              <div style={{ 
                background: '#0a0a0f',
                padding: '16px',
                borderRadius: '8px',
                fontSize: '13px',
                color: '#888'
              }}>
                <p style={{ margin: '0 0 8px' }}><strong style={{ color: '#fff' }}>Usage:</strong></p>
                <code style={{ fontFamily: 'monospace', color: '#6c63ff' }}>
                  curl -H "Authorization: Bearer {apiKey}" {API_BASE}/execute
                </code>
              </div>
            </div>
          </div>
        )}

        {/* Health Tab */}
        {activeTab === 'health' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <Server style={{ color: '#6c63ff' }} />
                <h3 style={{ margin: 0, color: '#fff' }}>API Status</h3>
              </div>
              <div style={{ 
                fontSize: '24px', 
                fontWeight: 'bold',
                color: health?.status === 'healthy' ? '#00c853' : '#ff4444'
              }}>
                {health?.status?.toUpperCase() || 'UNKNOWN'}
              </div>
            </div>

            <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <Layers style={{ color: '#6c63ff' }} />
                <h3 style={{ margin: 0, color: '#fff' }}>Blocks</h3>
              </div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff' }}>
                {health?.blocks_available || 0}
              </div>
            </div>

            <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <Shield style={{ color: '#6c63ff' }} />
                <h3 style={{ margin: 0, color: '#fff' }}>Security</h3>
              </div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00c853' }}>
                ACTIVE
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;