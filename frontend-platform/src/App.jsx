import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const API = 'https://ssdppg.onrender.com';

const PROJECTS = ['Diriyah Phase 1', 'Qiddam Tower', 'KAUST Lab', 'Riyadh Metro'];

const QUICK_ACTIONS = [
  { icon: '📄', text: 'Analyze PDF floorplan', prompt: 'Analyze this PDF floorplan and calculate material costs' },
  { icon: '📐', text: 'Extract measurements', prompt: 'Extract all measurements from this drawing' },
  { icon: '✅', text: 'Check code compliance', prompt: 'Check this blueprint for Saudi building code compliance' },
  { icon: '🌐', text: 'Translate to Arabic', prompt: 'Translate this construction document to Arabic' }
];

export default function App() {
  const [messages, setMessages] = useState([{ 
    role: 'assistant', 
    text: 'Hello! I can analyze documents, extract measurements, or help with construction projects. What would you like to do?', 
    showActions: true 
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeChain, setActiveChain] = useState([]);
  const [outcomes, setOutcomes] = useState([]);
  const [activeProject, setActiveProject] = useState('Diriyah Phase 1');
  const fileInput = useRef(null);
  const messagesEnd = useRef(null);

  useEffect(() => messagesEnd.current?.scrollIntoView({ behavior: 'smooth' }), [messages]);

  // Plug & Play: Auto-route to correct blocks based on input
  const routeBlocks = (text, file) => {
    const isPDF = file?.type === 'application/pdf';
    const isImage = file?.type?.startsWith('image/');
    const isConstruction = text.match(/concrete|steel|measurement|area|cost|bim|floorplan|masonry|blueprint/i);
    
    if (file && isPDF && isConstruction) return { 
      chain: ['pdf', 'construction', 'ai_core'], 
      display: ['PDF Extractor', 'Construction AI', 'AI Core'] 
    };
    if (file && isPDF) return { 
      chain: ['pdf', 'ocr', 'chat'], 
      display: ['PDF Reader', 'OCR', 'Chat'] 
    };
    if (file && isImage) return { 
      chain: ['ocr', 'chat'], 
      display: ['OCR Vision', 'Chat'] 
    };
    if (text.match(/search|find/i)) return { 
      chain: ['search', 'chat'], 
      display: ['Search', 'Chat'] 
    };
    if (text.match(/code|program/i)) return { 
      chain: ['code'], 
      display: ['Code'] 
    };
    return { chain: ['chat'], display: ['Chat'] };
  };

  const execute = async (text, file = null) => {
    if (!text.trim() && !file) return;
    
    const route = routeBlocks(text, file);
    setLoading(true);
    setActiveChain(route.display);
    
    setMessages(prev => [...prev, { 
      role: 'user', 
      text: file ? `📎 ${file.name}` : text 
    }]);
    setInput('');
    
    try {
      let fileUrl = null;
      if (file) {
        const form = new FormData();
        form.append('file', file);
        const up = await fetch(`${API}/v1/upload`, { method: 'POST', body: form }).then(r => r.json());
        fileUrl = up.url;
      }
      
      const result = await fetch(`${API}/v1/chain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chain: route.chain,
          input: fileUrl ? { url: fileUrl, text } : text
        })
      }).then(r => r.json());
      
      setMessages(prev => [...prev, { role: 'assistant', text: result.final_output || result.completion || 'Done' }]);
      
      if (result.quantities) {
        setOutcomes(prev => [{
          id: Date.now(),
          project: activeProject,
          area: result.quantities.floor_area_sqm,
          concrete: result.quantities.concrete_volume_m3,
          steel: result.quantities.steel_weight_kg,
          cost: result.ai_estimate?.total,
          time: new Date().toLocaleTimeString()
        }, ...prev]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', text: `Error: ${err.message}` }]);
    }
    
    setLoading(false);
    setActiveChain([]);
  };

  const send = () => execute(input);
  const handleFile = (e) => {
    const file = e.target.files[0];
    if (file) execute('', file);
  };

  return (
    <div className="app">
      {/* Block chain indicator - shows during execution */}
      {activeChain.length > 0 && (
        <div className="chain-indicator">
          <span className="pulse">⚡</span> Running: {activeChain.join(' → ')}
        </div>
      )}

      {/* LEFT: Projects Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <span className="logo">◆</span>
          <span>Cerebrum</span>
        </div>
        
        <button className="new-btn" onClick={() => {
          setMessages([{ role: 'assistant', text: 'New conversation started. How can I help?', showActions: true }]);
          setOutcomes([]);
        }}>
          + New Chat
        </button>
        
        <div className="section">Projects</div>
        <div className="projects">
          {PROJECTS.map(p => (
            <div key={p} className={`project ${activeProject === p ? 'active' : ''}`} onClick={() => setActiveProject(p)}>
              {activeProject === p && <span className="active-dot">●</span>}
              {p}
            </div>
          ))}
        </div>
        
        <div className="footer">
          <div className="drive">☁️ Google Drive Connected</div>
          <div className="user">
            <div className="avatar">U</div>
            <div>
              <div className="name">User</div>
              <div className="plan">Pro Plan</div>
            </div>
          </div>
        </div>
      </aside>

      {/* CENTER: Chat - Kimi Minimal Style */}
      <main className="chat">
        <header>
          <span className="project-name">{activeProject}</span>
          <span className="mode">Auto Mode</span>
        </header>

        <div className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <div className="bubble">{m.text}</div>
              
              {m.showActions && (
                <div className="quick-actions">
                  {QUICK_ACTIONS.map((a, idx) => (
                    <button key={idx} onClick={() => execute(a.prompt)}>
                      <span>{a.icon}</span> {a.text}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          
          {loading && !activeChain.length && <div className="thinking">Analyzing...</div>}
          <div ref={messagesEnd} />
        </div>

        <div className="input-area">
          <input type="file" ref={fileInput} style={{ display: 'none' }} onChange={handleFile} />
          <div className="input-box">
            <button className="upload" onClick={() => fileInput.current.click()}>+</button>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask anything or upload a file..."
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), send())}
            />
            <button className="send" onClick={send} disabled={loading}>
              {loading ? '◐' : '➤'}
            </button>
          </div>
        </div>
      </main>

      {/* RIGHT: Outcomes Panel */}
      <aside className="outcomes">
        <h3>Analysis Results</h3>
        
        {outcomes.length === 0 ? (
          <div className="empty">
            <div className="icon">📊</div>
            <p>Upload construction documents to see extracted measurements, material costs, and compliance reports.</p>
          </div>
        ) : (
          outcomes.map(o => (
            <div key={o.id} className="card">
              <div className="card-header">
                <span className="type">CONSTRUCTION</span>
                <span className="time">{o.time}</span>
              </div>
              <div className="doc">{o.project}</div>
              
              <div className="stats">
                {o.area && <div><label>Floor Area</label><value>{o.area} m²</value></div>}
                {o.concrete && <div><label>Concrete</label><value>{o.concrete} m³</value></div>}
                {o.steel && <div><label>Steel</label><value>{o.steel} kg</value></div>}
                {o.cost && <div className="cost"><label>Est. Cost</label><value>${o.cost}</value></div>}
              </div>
            </div>
          ))
        )}
      </aside>
    </div>
  );
}
