// Config-UI-Block - Settings and configuration
import { useState } from 'react';
import { CerebrumClient } from '../../api/client';

export const ConfigBlock: React.FC<{ apiKey: string }> = ({ apiKey }) => {
  const client = new CerebrumClient(apiKey);
  const [settings, setSettings] = useState({
    defaultProvider: 'deepseek',
    maxTokens: 2048,
    temperature: 0.7
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const save = async () => {
    setLoading(true);
    try {
      const data = await client.execute('config', null, settings);
      setMessage('Saved successfully');
      console.log(data);
    } catch (err: any) {
      setMessage('Error: ' + (err.message || 'Request failed'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ marginBottom: '10px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>Default LLM Provider</label>
        <select value={settings.defaultProvider} onChange={(e) => setSettings({...settings, defaultProvider: e.target.value})} style={{ padding: '8px', width: '100%' }}>
          <option value="deepseek">DeepSeek (Cheapest)</option>
          <option value="groq">Groq (Fastest)</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
      <div style={{ marginBottom: '10px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>Max Tokens: {settings.maxTokens}</label>
        <input type="range" min="256" max="4096" value={settings.maxTokens} onChange={(e) => setSettings({...settings, maxTokens: parseInt(e.target.value)})} style={{ width: '100%' }} />
      </div>
      <div style={{ marginBottom: '10px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>Temperature: {settings.temperature}</label>
        <input type="range" min="0" max="1" step="0.1" value={settings.temperature} onChange={(e) => setSettings({...settings, temperature: parseFloat(e.target.value)})} style={{ width: '100%' }} />
      </div>
      <button onClick={save} disabled={loading} style={{ padding: '8px 16px', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: loading ? 'not-allowed' : 'pointer' }}>
        {loading ? 'Saving...' : '💾 Save Config'}
      </button>
      {message && <div style={{ marginTop: '10px', fontSize: '12px', color: message.startsWith('Error') ? '#dc3545' : '#28a745' }}>{message}</div>}
    </div>
  );
};
