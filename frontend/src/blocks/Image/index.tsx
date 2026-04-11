// Image-UI-Block - Image analysis
import { useState } from 'react';

export const ImageBlock: React.FC<{ apiKey: string }> = ({ apiKey }) => {
  const [imagePath, setImagePath] = useState('');
  const [description, setDescription] = useState('');
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const analyze = async () => {
    // Placeholder
    setDescription('Image analysis result would appear here...');
  };

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
        <input type="text" value={imagePath} onChange={(e) => setImagePath(e.target.value)} placeholder="Image path..." style={{ flex: 1, padding: '8px' }} />
        <button onClick={analyze} style={{ padding: '8px 16px' }}>🖼️ Analyze</button>
      </div>
      {description && <div style={{ padding: '10px', background: '#f5f5f5', borderRadius: '4px' }}>{description}</div>}
    </div>
  );
};
