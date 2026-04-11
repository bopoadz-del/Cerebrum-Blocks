// Code-UI-Block - Code execution
import { useState } from 'react';

export const CodeBlock: React.FC<{ apiKey: string }> = ({ apiKey }) => {
  const [code, setCode] = useState('print("Hello World")');
  const [language, setLanguage] = useState('python');
  const [output, setOutput] = useState('');
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const run = async () => {
    // Placeholder
    setOutput('Hello World\n[Execution simulated]');
  };

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ marginBottom: '5px' }}>
        <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{ padding: '5px' }}>
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="bash">Bash</option>
        </select>
      </div>
      <textarea value={code} onChange={(e) => setCode(e.target.value)} style={{ width: '100%', height: '100px', padding: '8px', fontFamily: 'monospace', fontSize: '12px', marginBottom: '5px' }} />
      <button onClick={run} style={{ padding: '8px 16px', marginBottom: '10px' }}>▶️ Run</button>
      {output && <pre style={{ padding: '10px', background: '#1e1e1e', color: '#d4d4d4', borderRadius: '4px', fontSize: '12px' }}>{output}</pre>}
    </div>
  );
};
