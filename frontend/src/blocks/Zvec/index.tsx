// Zvec-UI-Block - Zero-shot embeddings
import { useState } from 'react';
import { CerebrumClient } from '../../api/client';

interface ZvecBlockProps {
  apiKey: string;
}

export const ZvecBlock: React.FC<ZvecBlockProps> = ({ apiKey }) => {
  const client = new CerebrumClient(apiKey);
  const [text1, setText1] = useState('');
  const [text2, setText2] = useState('');
  const [similarity, setSimilarity] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const compare = async () => {
    if (!text1 || !text2) return;
    setLoading(true);
    try {
      const data = await client.execute('zvec', null, { text1, text2, operation: 'similarity' });
      setSimilarity(data.similarity);
    } catch (err: any) {
      console.error('Zvec failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ marginBottom: '10px' }}>
        <textarea value={text1} onChange={(e) => setText1(e.target.value)} placeholder="Text 1..." style={{ width: '100%', padding: '8px', marginBottom: '5px', height: '60px' }} />
        <textarea value={text2} onChange={(e) => setText2(e.target.value)} placeholder="Text 2..." style={{ width: '100%', padding: '8px', marginBottom: '5px', height: '60px' }} />
        <button onClick={compare} disabled={loading} style={{ padding: '8px 16px' }}>{loading ? '...' : '🧮 Compare'}</button>
      </div>
      {similarity !== null && (
        <div style={{ padding: '10px', background: '#e3f2fd', borderRadius: '4px', textAlign: 'center' }}>
          Similarity: <strong>{(similarity * 100).toFixed(1)}%</strong>
        </div>
      )}
    </div>
  );
};
