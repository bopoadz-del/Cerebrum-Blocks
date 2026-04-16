// Image-UI-Block - Image analysis
import { useState } from 'react';
import { CerebrumClient } from '../../api/client';

export const ImageBlock: React.FC<{ apiKey: string }> = ({ apiKey }) => {
  const client = new CerebrumClient(apiKey);
  const [imagePath, setImagePath] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    if (!imagePath.trim()) return;
    setLoading(true);
    try {
      const data = await client.execute('image', imagePath, { action: 'analyze' });
      setDescription(JSON.stringify(data, null, 2));
    } catch (err: any) {
      setDescription('Error: ' + (err.message || 'Request failed'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
        <input type="text" value={imagePath} onChange={(e) => setImagePath(e.target.value)} placeholder="Image path..." style={{ flex: 1, padding: '8px' }} />
        <button onClick={analyze} disabled={loading} style={{ padding: '8px 16px' }}>{loading ? '...' : '🖼️ Analyze'}</button>
      </div>
      {description && <pre style={{ padding: '10px', background: '#1e1e1e', color: '#d4d4d4', borderRadius: '4px', fontSize: '12px', overflow: 'auto', maxHeight: '200px' }}>{description}</pre>}
    </div>
  );
};
