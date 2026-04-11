// Voice-UI-Block - TTS/STT
import { useState } from 'react';

export const VoiceBlock: React.FC<{ apiKey: string }> = ({ apiKey }) => {
  const [text, setText] = useState('');
  const [mode, setMode] = useState<'tts' | 'stt'>('tts');
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const process = async () => {
    // Placeholder for voice processing
    console.log('Voice processing:', mode, text);
  };

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ marginBottom: '10px' }}>
        <select value={mode} onChange={(e) => setMode(e.target.value as any)} style={{ padding: '8px', marginRight: '10px' }}>
          <option value="tts">Text to Speech</option>
          <option value="stt">Speech to Text</option>
        </select>
      </div>
      {mode === 'tts' ? (
        <>
          <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Enter text..." style={{ width: '100%', padding: '8px', height: '80px', marginBottom: '5px' }} />
          <button onClick={process} style={{ padding: '8px 16px' }}>🔊 Speak</button>
        </>
      ) : (
        <div style={{ padding: '20px', textAlign: 'center', background: '#f5f5f5', borderRadius: '4px' }}>
          <button style={{ padding: '12px 24px', borderRadius: '50%' }}>🎙️ Record</button>
        </div>
      )}
    </div>
  );
};
