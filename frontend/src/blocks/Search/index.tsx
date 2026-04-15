// Search-UI-Block - Web search
import { useState } from 'react';
import { API } from '../../api';

interface SearchBlockProps {
  apiKey: string;
  onResult?: (results: any[]) => void;
}

export const SearchBlock: React.FC<SearchBlockProps> = ({ apiKey, onResult }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const search = async () => {
    if (!query) return;
    setLoading(true);
    try {
      const data = await API.call('/v1/search', { query, n_results: 5 });
      setResults(data.results || []);
      onResult?.(data.results || []);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && search()} placeholder="Search the web..." style={{ flex: 1, padding: '8px' }} />
        <button onClick={search} disabled={loading} style={{ padding: '8px 16px' }}>{loading ? '...' : '🔎 Search'}</button>
      </div>
      {results.length > 0 && (
        <div style={{ border: '1px solid #eee', borderRadius: '4px' }}>
          {results.map((r, i) => (
            <div key={i} style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
              <a href={r.url} target="_blank" rel="noopener" style={{ fontWeight: 'bold' }}>{r.title}</a>
              <div style={{ fontSize: '12px', color: '#666' }}>{r.snippet}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
