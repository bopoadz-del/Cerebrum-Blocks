// Voice-UI-Block - TTS/STT
import { useState } from 'react';
import { CerebrumClient } from '../../api/client';

export const VoiceBlock: React.FC<{ apiKey: string }> = ({ apiKey }) => {
  const client = new CerebrumClient(apiKey);
  const [text, setText] = useState('');
  const [mode, setMode] = useState<'tts' | 'stt'>('tts');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const process = async () => {
    setLoading(true);
    try {
      const data = await client.execute('voice', mode === 'tts' ? text : null, { mode });
      setResult(JSON.stringify(data, null, 2));
    } catch (err: any) {
      setResult('Error: ' + (err.message || 'Request failed'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ marginBottom: '10px' }}>
        <select value={mode} onChange={(e) => setMode(e.target.value as any)} style={{ padding: '8px', marginRight: '10px' }}>
          <option value="tts">Text to Speech</option>
          <option value="stt">Speech to Text</option>
        </select>
        <button onClick={process} disabled={loading} style={{ padding: '8px 16px' }}>{loading ? '...' : (mode === 'tts' ? '🔊 Speak' : '🎙️ Process')}</button>
      </div>
      {mode === 'tts' ? (
        <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Enter text..." style={{ width: '100%', padding: '8px', height: '80px', marginBottom: '5px' }} />
      ) : (
        <div style={{ padding: '20px', textAlign: 'center', background: '#f5f5f5', borderRadius: '4px', marginBottom: '5px' }}>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '10px' }}>Upload or record audio to transcribe</div>
        </div>
      )}
      {result && <pre style={{ padding: '10px', background: '#1e1e1e', color: '#d4d4d4', borderRadius: '4px', fontSize: '12px', overflow: 'auto', maxHeight: '150px' }}>{result}</pre>}
    </div>
  );
};
