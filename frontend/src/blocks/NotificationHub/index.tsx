import { useState } from 'react';

interface NotificationHubBlockProps {
  apiKey: string;
}

const channels = [
  { value: 'telegram', label: '📨 Telegram' },
  { value: 'email', label: '✉️ Email' },
  { value: 'webhook', label: '🔗 Webhook' },
  { value: 'slack', label: '💬 Slack' },
];

export const NotificationHubBlock: React.FC<NotificationHubBlockProps> = ({ apiKey }) => {
  const [channel, setChannel] = useState('telegram');
  const [to, setTo] = useState('');
  const [message, setMessage] = useState('');
  const [subject, setSubject] = useState('');
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const send = async () => {
    setLoading(true);
    try {
      const body: any = { channel, to, message };
      if (subject) body.subject = subject;
      if (url) body.url = url;
      const res = await fetch(`${API_BASE}/notify/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify(body),
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
      <select
        value={channel}
        onChange={(e) => setChannel(e.target.value)}
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', marginBottom: '8px', boxSizing: 'border-box' }}
      >
        {channels.map((c) => (
          <option key={c.value} value={c.value}>{c.label}</option>
        ))}
      </select>
      <input
        type="text"
        value={to}
        onChange={(e) => setTo(e.target.value)}
        placeholder={channel === 'email' ? 'user@example.com' : channel === 'telegram' ? 'Chat ID' : 'Recipient / Channel'}
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', marginBottom: '8px', boxSizing: 'border-box' }}
      />
      {channel === 'email' && (
        <input
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Subject"
          style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', marginBottom: '8px', boxSizing: 'border-box' }}
        />
      )}
      {(channel === 'webhook' || channel === 'slack') && (
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Webhook URL"
          style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', marginBottom: '8px', boxSizing: 'border-box' }}
        />
      )}
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Message..."
        rows={3}
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', marginBottom: '8px', boxSizing: 'border-box' }}
      />
      <button
        onClick={send}
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
        {loading ? 'Sending...' : '📤 Send'}
      </button>
      {result && (
        <div style={{ marginTop: '10px', fontSize: '12px' }}>
          <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: '10px', borderRadius: '4px', fontSize: '11px', overflow: 'auto', maxHeight: '150px', margin: 0 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
