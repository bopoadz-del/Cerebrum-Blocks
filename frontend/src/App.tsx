import { useState } from 'react';
import { 
  ChatBlock, VectorBlock, StorageBlock, QueueBlock,
  PDFBlock, OCRBlock, WebBlock, SearchBlock, ZvecBlock,
  VoiceBlock, ImageBlock, TranslateBlock, CodeBlock,
  FailoverBlock, ConfigBlock
} from './blocks';

function App() {
  const API_KEY = 'cb_dev_key';
  const [activeJob, setActiveJob] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<any>(null);

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1>🧠 Cerebrum Blocks - Universal AI Platform</h1>
      <p>20+ Blocks. One Platform. Infinite Possibilities.</p>

      {/* System Health */}
      <div style={{ marginBottom: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
        <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>
          🛡️ System Health
        </div>
        <FailoverBlock apiKey={API_KEY} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {/* AI Core Blocks */}
        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>💬 Chat</div>
          <ChatBlock apiKey={API_KEY} provider="deepseek" maxHeight="300px" />
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>🔍 Vector Search</div>
          <VectorBlock apiKey={API_KEY} />
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>💾 Storage</div>
          <StorageBlock apiKey={API_KEY} onFileSelect={setSelectedFile} />
        </div>

        {/* Document Processing */}
        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>📄 PDF</div>
          <PDFBlock apiKey={API_KEY} />
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>👁️ OCR</div>
          <OCRBlock apiKey={API_KEY} />
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>🖼️ Image</div>
          <ImageBlock apiKey={API_KEY} />
        </div>

        {/* Web & Search */}
        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>🕸️ Web</div>
          <WebBlock apiKey={API_KEY} />
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>🔎 Search</div>
          <SearchBlock apiKey={API_KEY} />
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>🧮 Zvec</div>
          <ZvecBlock apiKey={API_KEY} />
        </div>

        {/* Tools */}
        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>🌐 Translate</div>
          <TranslateBlock apiKey={API_KEY} />
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>💻 Code</div>
          <CodeBlock apiKey={API_KEY} />
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>🔊 Voice</div>
          <VoiceBlock apiKey={API_KEY} />
        </div>

        {/* Config */}
        <div style={{ border: '1px solid #ddd', borderRadius: '8px' }}>
          <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>⚙️ Config</div>
          <ConfigBlock apiKey={API_KEY} />
        </div>

        {/* Queue Monitor */}
        {activeJob && (
          <div style={{ gridColumn: 'span 2', border: '1px solid #ddd', borderRadius: '8px' }}>
            <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>📬 Queue</div>
            <QueueBlock apiKey={API_KEY} jobId={activeJob} />
          </div>
        )}
      </div>

      {/* Usage Example */}
      <div style={{ marginTop: '30px', padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
        <h4>3 Lines of Code Per Block:</h4>
        <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: '15px', borderRadius: '4px', overflow: 'auto' }}>
{`import { ChatBlock, VectorBlock, PDFBlock } from './blocks';

<ChatBlock apiKey="cb_key" provider="deepseek" />
<VectorBlock apiKey="cb_key" onResultsSelect={handleSelect} />
<PDFBlock apiKey="cb_key" onExtract={handleExtract} />`}
        </pre>
      </div>
    </div>
  );
}

export default App;
