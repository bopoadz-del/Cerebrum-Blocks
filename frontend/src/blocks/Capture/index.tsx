import { useState, useRef } from 'react';

interface CaptureBlockProps {
  apiKey: string;
}

export const CaptureBlock: React.FC<CaptureBlockProps> = ({ apiKey }) => {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('source', 'web');
      const res = await fetch(`${API_BASE}/capture/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${apiKey}` },
        body: form,
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
      <input
        type="file"
        accept="image/*"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        style={{
          width: '100%',
          padding: '10px',
          background: '#6c757d',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          marginBottom: '10px',
        }}
      >
        {file ? `📸 ${file.name}` : '📁 Select Image'}
      </button>
      <button
        onClick={handleUpload}
        disabled={!file || loading}
        style={{
          width: '100%',
          padding: '10px',
          background: !file || loading ? '#6c757d' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: !file || loading ? 'not-allowed' : 'pointer',
          fontWeight: 'bold',
        }}
      >
        {loading ? 'Processing...' : '▶️ Capture & Structure'}
      </button>
      {result && (
        <div style={{ marginTop: '10px' }}>
          {result.capture_id && (
            <div style={{ fontSize: '12px', color: '#28a745', marginBottom: '5px' }}>
              ✅ ID: <code>{result.capture_id}</code>
            </div>
          )}
          {result.summary && (
            <div style={{ fontSize: '12px', marginBottom: '5px' }}>
              <strong>Summary:</strong> {result.summary}
            </div>
          )}
          {result.tags && (
            <div style={{ fontSize: '12px', marginBottom: '5px' }}>
              {result.tags.map((t: string) => (
                <span key={t} style={{ display: 'inline-block', padding: '2px 6px', background: '#e3f2fd', borderRadius: '4px', margin: '2px', fontSize: '11px' }}>{t}</span>
              ))}
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
