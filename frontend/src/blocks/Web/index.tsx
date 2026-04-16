// Web-UI-Block - Web scraping
import { useState } from 'react';
import { CerebrumClient } from '../../api/client';

interface WebBlockProps {
  apiKey: string;
  onFetch?: (result: any) => void;
}

export const WebBlock: React.FC<WebBlockProps> = ({ apiKey, onFetch }) => {
  const client = new CerebrumClient(apiKey);
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchPage = async () => {
    if (!url) return;
    setLoading(true);
    try {
      const data = await client.execute('web', null, { url });
      setResult(data);
      onFetch?.(data);
    } catch (err: any) {
      console.error('Web fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
        <input type="text" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" style={{ flex: 1, padding: '8px' }} />
        <button onClick={fetchPage} disabled={loading} style={{ padding: '8px 16px' }}>{loading ? '...' : '🕸️ Fetch'}</button>
      </div>
      {result?.content && (
        <div style={{ padding: '10px', background: '#f5f5f5', borderRadius: '4px', fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}>
          Status: {result.status}<br/>
          {result.content.substring(0, 1000)}...
        </div>
      )}
    </div>
  );
};
