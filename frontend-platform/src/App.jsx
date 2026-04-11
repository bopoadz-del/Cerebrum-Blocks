import React, { useState, useRef, useEffect, useCallback } from 'react';
import './App.css';

// Block imports
import { UIBlock } from './blocks/UIBlock.js';
import APIBlock from './ui-blocks/system/APIBlock.js';
import ChainBlock from './ui-blocks/chain/ChainBlock.js';
import FileUploadBlock from './ui-blocks/input/FileUploadBlock.js';
import ChatInputBlock from './ui-blocks/input/ChatInputBlock.js';
import VoiceInputBlock from './ui-blocks/input/VoiceInputBlock.js';
import ChatWindowBlock from './ui-blocks/output/ChatWindowBlock.js';
import OutcomesBlock from './ui-blocks/output/OutcomesBlock.js';

const PROJECTS = ['Diriyah Phase 1', 'Qiddam Tower', 'KAUST Lab', 'Riyadh Metro'];

const QUICK_ACTIONS = [
  { icon: '📄', text: 'Analyze PDF floorplan', prompt: 'Analyze this PDF floorplan and calculate material costs' },
  { icon: '📐', text: 'Extract measurements', prompt: 'Extract all measurements from this drawing' },
  { icon: '✅', text: 'Check code compliance', prompt: 'Check this blueprint for Saudi building code compliance' },
  { icon: '🌐', text: 'Translate to Arabic', prompt: 'Translate this construction document to Arabic' }
];

export default function App() {
  // React state
  const [messages, setMessages] = useState([{ 
    id: 'welcome',
    role: 'assistant', 
    content: 'Hello! I can analyze documents, extract measurements, or help with construction projects. What would you like to do?', 
    showActions: true 
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeChain, setActiveChain] = useState(null);
  const [outcomes, setOutcomes] = useState([]);
  const [activeProject, setActiveProject] = useState('Diriyah Phase 1');
  const [isRecording, setIsRecording] = useState(false);
  
  const fileInput = useRef(null);
  const messagesEnd = useRef(null);

  // Initialize blocks (singleton pattern)
  const blocks = useRef({});
  
  useEffect(() => {
    // Create block instances
    const api = new APIBlock({});
    const chain = new ChainBlock({ api });
    const fileUpload = new FileUploadBlock({ api, chain });
    const chatInput = new ChatInputBlock({ api, chain });
    const voiceInput = new VoiceInputBlock({ api });
    const chatWindow = new ChatWindowBlock({
      onMessage: (msg) => setMessages(prev => [...prev, msg]),
      onChain: (indicator) => setActiveChain(indicator.active ? indicator : null)
    });
    const outcomesBlock = new OutcomesBlock({
      onOutcome: (outcome) => setOutcomes(prev => [outcome, ...prev])
    });

    // Wire up chain events
    chain.on('chain:start', ({ display }) => {
      setActiveChain({ chain: display, step: 0 });
    });
    
    chain.on('step:start', ({ step, total, display }) => {
      setActiveChain(prev => prev ? { ...prev, step, total, current: display } : null);
    });
    
    chain.on('chain:complete', () => {
      setActiveChain(null);
    });

    // Wire up outcomes from chain results
    chain.on('chain:complete', (result) => {
      const constructionOutcomes = outcomesBlock.parseConstructionResult(result);
      constructionOutcomes.forEach(o => {
        outcomesBlock.addOutcome({ ...o, project: activeProject }, { category: o.type });
      });
    });

    blocks.current = {
      api,
      chain,
      fileUpload,
      chatInput,
      voiceInput,
      chatWindow,
      outcomes: outcomesBlock
    };

    // Add welcome message to chatWindow
    chatWindow.messages = messages;

    return () => {
      // Cleanup
      Object.values(blocks.current).forEach(block => {
        if (block.listeners) block.listeners = {};
      });
    };
  }, []);

  // Auto-scroll messages
  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle text input submission
  const handleSend = useCallback(async () => {
    if (!input.trim() || loading) return;
    
    setLoading(true);
    const text = input;
    setInput('');

    // Add user message to UI immediately
    const userMsg = { id: Date.now(), role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);

    try {
      const result = await blocks.current.chatInput.execute(text);
      
      // Add assistant response
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: result.response,
        chain: result.chain
      }]);

    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'error',
        content: `Error: ${error.message}`
      }]);
    }

    setLoading(false);
  }, [input, loading]);

  // Handle file upload
  const handleFile = useCallback(async (e) => {
    const file = e.target.files[0];
    if (!file || loading) return;

    setLoading(true);

    // Add file message to UI
    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      content: `📎 ${file.name}`
    }]);

    try {
      const result = await blocks.current.fileUpload.execute(file);
      
      // Add assistant response
      const response = result.chain?.final_output?.completion 
        || result.chain?.final_output 
        || 'File processed successfully';

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: response,
        chain: result.chain?.chain
      }]);

    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'error',
        content: `Error processing file: ${error.message}`
      }]);
    }

    setLoading(false);
  }, [loading]);

  // Handle voice recording
  const handleVoice = useCallback(async () => {
    if (isRecording) {
      // Stop recording
      setLoading(true);
      try {
        const result = await blocks.current.voiceInput.execute('stop');
        setInput(prev => prev + ' ' + result.text);
      } catch (error) {
        console.error('Voice error:', error);
      }
      setIsRecording(false);
      setLoading(false);
    } else {
      // Start recording
      try {
        await blocks.current.voiceInput.execute('start');
        setIsRecording(true);
      } catch (error) {
        console.error('Voice error:', error);
      }
    }
  }, [isRecording, loading]);

  // Handle quick action
  const handleQuickAction = useCallback(async (prompt) => {
    if (loading) return;
    setInput(prompt);
    // Small delay to show the prompt in input, then send
    setTimeout(() => handleSend(), 100);
  }, [loading, handleSend]);

  // New chat
  const handleNewChat = useCallback(() => {
    blocks.current.chatInput.clear();
    blocks.current.outcomes.clearOutcomes();
    setMessages([{ 
      id: 'welcome',
      role: 'assistant', 
      content: 'New conversation started. How can I help?', 
      showActions: true 
    }]);
    setOutcomes([]);
  }, []);

  return (
    <div className="app">
      {/* Chain indicator - shows executing blocks */}
      {activeChain && (
        <div className="chain-indicator">
          <span className="pulse">⚡</span>
          <span className="chain-text">
            Running: {activeChain.chain.join(' → ')}
            {activeChain.current && (
              <span className="current"> ({activeChain.current})</span>
            )}
          </span>
        </div>
      )}

      {/* LEFT: Projects Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <span className="logo">◆</span>
          <span>Cerebrum</span>
        </div>
        
        <button className="new-btn" onClick={handleNewChat}>
          + New Chat
        </button>
        
        <div className="section">Projects</div>
        <div className="projects">
          {PROJECTS.map(p => (
            <div 
              key={p} 
              className={`project ${activeProject === p ? 'active' : ''}`} 
              onClick={() => setActiveProject(p)}
            >
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

      {/* CENTER: Chat */}
      <main className="chat">
        <header>
          <span className="project-name">{activeProject}</span>
          <span className="mode">Auto Mode</span>
        </header>

        <div className="messages">
          {messages.map((m) => (
            <div key={m.id} className={`msg ${m.role}`}>
              <div className="bubble">{m.content}</div>
              
              {m.chain && (
                <div className="chain-tag">
                  {m.chain.map((b, i) => (
                    <span key={i} className="tag">{b}</span>
                  ))}
                </div>
              )}
              
              {m.showActions && (
                <div className="quick-actions">
                  {QUICK_ACTIONS.map((a, idx) => (
                    <button key={idx} onClick={() => handleQuickAction(a.prompt)}>
                      <span>{a.icon}</span> {a.text}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          
          {loading && <div className="thinking">Processing...</div>}
          <div ref={messagesEnd} />
        </div>

        <div className="input-area">
          <input 
            type="file" 
            ref={fileInput} 
            style={{ display: 'none' }} 
            onChange={handleFile}
            accept=".pdf,.jpg,.jpeg,.png,.webp,.mp3,.wav,.webm"
          />
          <div className="input-box">
            <button className="upload" onClick={() => fileInput.current.click()}>+</button>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask anything or upload a file..."
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={loading}
            />
            <button 
              className={`voice ${isRecording ? 'recording' : ''}`} 
              onClick={handleVoice}
              disabled={loading}
            >
              {isRecording ? '◉' : '🎤'}
            </button>
            <button className="send" onClick={handleSend} disabled={loading || !input.trim()}>
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
                <span className="type">{o.type?.toUpperCase() || 'RESULT'}</span>
                <span className="time">{o.timestamp?.toLocaleTimeString?.() || new Date().toLocaleTimeString()}</span>
              </div>
              <div className="doc">{o.project}</div>
              
              <div className="stats">
                {o.area && (
                  <div>
                    <label>Floor Area</label>
                    <value>{typeof o.area === 'number' ? o.area.toLocaleString() : o.area} m²</value>
                  </div>
                )}
                {o.concrete && (
                  <div>
                    <label>Concrete</label>
                    <value>{typeof o.concrete === 'number' ? o.concrete.toLocaleString() : o.concrete} m³</value>
                  </div>
                )}
                {o.steel && (
                  <div>
                    <label>Steel</label>
                    <value>{typeof o.steel === 'number' ? o.steel.toLocaleString() : o.steel} kg</value>
                  </div>
                )}
                {o.cost && (
                  <div className="cost">
                    <label>Est. Cost</label>
                    <value>${typeof o.cost === 'number' ? o.cost.toLocaleString() : o.cost}</value>
                  </div>
                )}
                {o.confidence && (
                  <div className="confidence">
                    <label>Confidence</label>
                    <value>{Math.round(o.confidence * 100)}%</value>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </aside>
    </div>
  );
}
