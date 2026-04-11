import { useState } from 'react';
import { 
  // Core AI Blocks
  ChatBlock, VectorBlock, StorageBlock, QueueBlock,
  PDFBlock, OCRBlock, WebBlock, SearchBlock, ZvecBlock,
  VoiceBlock, ImageBlock, TranslateBlock, CodeBlock,
  // Domain Containers (Layer 3) - shown as cards, not block components
  // BIMBlock, DroneBlock moved to card-based UI
  // Drive Blocks
  GoogleDriveBlock, OneDriveBlock, AndroidDriveBlock,
  // Infrastructure Blocks (Layer 0)
  FailoverBlock, ConfigBlock, AuthBlock, MemoryBlock, 
  MonitoringBlock, HALBlock,
  // Integration Blocks
  DatabaseBlock, EmailBlock, WebhookBlock, WorkflowBlock, BillingBlock
} from './blocks';

// Domain Container Placeholder Components (until real ones are built)
const DomainContainerCard = ({ 
  name, 
  icon, 
  description, 
  price, 
  status,
  features,
  color 
}: { 
  name: string; 
  icon: string; 
  description: string;
  price: string;
  status: 'live' | 'beta' | 'coming';
  features: string[];
  color: string;
}) => (
  <div style={{ 
    border: '1px solid #ddd', 
    borderRadius: '12px',
    overflow: 'hidden',
    background: 'white',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    transition: 'transform 0.2s, box-shadow 0.2s',
  }}>
    <div style={{ 
      padding: '16px', 
      background: `linear-gradient(135deg, ${color}15, ${color}05)`,
      borderBottom: `2px solid ${color}`,
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    }}>
      <span style={{ fontSize: '32px' }}>{icon}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#333' }}>{name}</div>
        <div style={{ 
          fontSize: '11px', 
          padding: '2px 8px',
          borderRadius: '12px',
          background: status === 'live' ? '#00c853' : status === 'beta' ? '#ff9100' : '#9e9e9e',
          color: 'white',
          display: 'inline-block',
          marginTop: '4px',
          textTransform: 'uppercase',
          fontWeight: 'bold'
        }}>
          {status}
        </div>
      </div>
      <div style={{ 
        fontSize: '20px', 
        fontWeight: 'bold', 
        color: color 
      }}>{price}</div>
    </div>
    <div style={{ padding: '16px' }}>
      <p style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#666', lineHeight: '1.5' }}>
        {description}
      </p>
      <div style={{ fontSize: '11px', color: '#999', marginBottom: '8px', fontWeight: 'bold' }}>
        KEY FEATURES:
      </div>
      <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '12px', color: '#555' }}>
        {features.map((f, i) => (
          <li key={i} style={{ marginBottom: '4px' }}>{f}</li>
        ))}
      </ul>
    </div>
  </div>
);

// Platform Service Card
const PlatformServiceCard = ({
  name,
  icon,
  description,
  layer,
  features,
  color
}: {
  name: string;
  icon: string;
  description: string;
  layer: string;
  features: string[];
  color: string;
}) => (
  <div style={{ 
    border: '1px solid #ddd', 
    borderRadius: '12px',
    overflow: 'hidden',
    background: 'white',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  }}>
    <div style={{ 
      padding: '12px 16px', 
      background: color,
      color: 'white',
      display: 'flex',
      alignItems: 'center',
      gap: '10px'
    }}>
      <span style={{ fontSize: '24px' }}>{icon}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{name}</div>
        <div style={{ fontSize: '10px', opacity: 0.9 }}>{layer}</div>
      </div>
    </div>
    <div style={{ padding: '14px' }}>
      <p style={{ margin: '0 0 10px 0', fontSize: '12px', color: '#666' }}>
        {description}
      </p>
      <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '11px', color: '#555' }}>
        {features.map((f, i) => (
          <li key={i} style={{ marginBottom: '3px' }}>{f}</li>
        ))}
      </ul>
    </div>
  </div>
);

function App() {
  const API_KEY = 'cb_dev_key';
  const [activeJob] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<
    'ai' | 'domain' | 'platform' | 'infrastructure' | 'storage'
  >('domain');

  const TabButton = ({ 
    tab, 
    label, 
    icon,
    badge
  }: { 
    tab: typeof activeTab; 
    label: string; 
    icon: string;
    badge?: string;
  }) => (
    <button
      onClick={() => setActiveTab(tab)}
      style={{
        padding: '12px 24px',
        background: activeTab === tab ? '#6c63ff' : '#f5f5f5',
        color: activeTab === tab ? 'white' : '#555',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
        fontWeight: activeTab === tab ? 'bold' : 'normal',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '14px',
        transition: 'all 0.2s',
        boxShadow: activeTab === tab ? '0 4px 12px rgba(108, 99, 255, 0.3)' : 'none',
        position: 'relative'
      }}
    >
      {icon} {label}
      {badge && (
        <span style={{
          position: 'absolute',
          top: '-6px',
          right: '-6px',
          background: '#ff4081',
          color: 'white',
          fontSize: '10px',
          padding: '2px 6px',
          borderRadius: '10px',
          fontWeight: 'bold'
        }}>
          {badge}
        </span>
      )}
    </button>
  );

  // Domain Container Data
  const domainContainers = [
    {
      name: 'Construction',
      icon: '🏗️',
      description: 'BIM processing, PDF extraction, QA inspection, and progress tracking for AEC industry.',
      price: '$299/mo',
      status: 'live' as const,
      features: ['BIM Analysis (IFC/DWG)', 'PDF Plan Extraction', 'QA Defect Detection', 'Progress Tracking', 'Cost Estimation'],
      color: '#ff6b35'
    },
    {
      name: 'Medical',
      icon: '🏥',
      description: 'HIPAA-compliant DICOM processing, clinical entity extraction, and report generation.',
      price: '$499/mo',
      status: 'live' as const,
      features: ['DICOM Processing', 'PHI Anonymization', 'Clinical Entity Extraction', 'HIPAA Validation', 'Radiology Reports'],
      color: '#00b4d8'
    },
    {
      name: 'Legal',
      icon: '⚖️',
      description: 'Contract analysis, precedent validation, and legal brief generation for law firms.',
      price: '$399/mo',
      status: 'live' as const,
      features: ['Contract Analysis', 'Clause Extraction', 'Precedent Validation', 'Risk Assessment', 'Brief Generation'],
      color: '#7b2cbf'
    },
    {
      name: 'Finance',
      icon: '💰',
      description: 'Risk analysis, SOX/MiFID compliance, and regulatory reporting for trading desks.',
      price: '$599/mo',
      status: 'live' as const,
      features: ['Risk Analysis (VaR)', 'SOX/MiFID Compliance', 'Trade Processing', 'Regulatory Reporting', 'Stress Testing'],
      color: '#2d6a4f'
    },
    {
      name: 'Education',
      icon: '🎓',
      description: 'Course content processing, assessment generation, and student analytics.',
      price: '$199/mo',
      status: 'coming' as const,
      features: ['Content Processing', 'Quiz Generation', 'Student Analytics', 'Grade Automation', 'Learning Paths'],
      color: '#ffaa00'
    },
    {
      name: 'Government',
      icon: '🏛️',
      description: 'Smart city data processing, permit validation, and public records management.',
      price: '$799/mo',
      status: 'coming' as const,
      features: ['Permit Processing', 'Public Records', 'Compliance Checks', 'GIS Integration', 'Citizen Services'],
      color: '#5c677d'
    }
  ];

  // Platform Services Data
  const platformServices = [
    {
      name: 'Security',
      icon: '🔐',
      description: 'API key management, rate limiting, sandbox validation, and audit logging.',
      layer: 'Layer 1 - Security',
      features: ['API Key Auth', 'Rate Limiting', 'Sandbox Check', 'Audit Logging'],
      color: '#d00000'
    },
    {
      name: 'AI Core',
      icon: '🤖',
      description: 'Adaptive routing, provider failover, and performance leaderboard.',
      layer: 'Layer 2 - AI Brain',
      features: ['Adaptive Routing', 'Provider Failover', 'Leaderboard', 'Circuit Breaker'],
      color: '#0077b6'
    },
    {
      name: 'Store',
      icon: '🏪',
      description: 'Block discovery, reviews, payment split, and validation services.',
      layer: 'Layer 4 - Marketplace',
      features: ['Block Discovery', 'Reviews', 'Lego Tax (20%)', 'Validation'],
      color: '#ff006e'
    }
  ];

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto', background: '#fafafa', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: '#1a1a2e' }}>
          🧠 Cerebrum Blocks
        </h1>
        <p style={{ margin: '0 0 16px 0', color: '#666', fontSize: '14px' }}>
          <strong>Domain Adapter Protocol (DAP)</strong> — One platform. Swappable industries. Infinite possibilities.
        </p>
        
        {/* Architecture Legend */}
        <div style={{ 
          display: 'flex', 
          gap: '20px', 
          flexWrap: 'wrap',
          padding: '12px 16px',
          background: 'white',
          borderRadius: '8px',
          border: '1px solid #e0e0e0',
          fontSize: '12px'
        }}>
          <div><strong>22 Total Blocks:</strong></div>
          <div>🔴 <strong>4</strong> Domain Containers (Layer 3)</div>
          <div>🔵 <strong>3</strong> Platform Services (L1, L2, L4)</div>
          <div>🟢 <strong>15</strong> Core AI Blocks</div>
          <div style={{ marginLeft: 'auto', color: '#6c63ff', fontWeight: 'bold' }}>
            Lego Tax: 20% Platform / 80% Creator
          </div>
        </div>
      </div>

      {/* System Health */}
      <div style={{ marginBottom: '24px', border: '1px solid #ddd', borderRadius: '12px', overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', background: '#1a1a2e', color: 'white', fontWeight: 'bold' }}>
          🛡️ System Health & Provider Leaderboard
        </div>
        <div style={{ padding: '16px', background: 'white' }}>
          <FailoverBlock apiKey={API_KEY} />
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <TabButton tab="domain" label="Domain Containers" icon="🏭" badge="4 NEW" />
        <TabButton tab="ai" label="Core AI Blocks" icon="🤖" />
        <TabButton tab="platform" label="Platform Services" icon="⚙️" />
        <TabButton tab="infrastructure" label="Infrastructure" icon="🔧" />
        <TabButton tab="storage" label="Storage & Drives" icon="💾" />
      </div>

      {/* Domain Containers Tab - THE MONEY MAKERS */}
      {activeTab === 'domain' && (
        <div>
          <div style={{ 
            background: 'linear-gradient(135deg, #6c63ff, #ff6b35)', 
            color: 'white',
            padding: '20px',
            borderRadius: '12px',
            marginBottom: '24px'
          }}>
            <h2 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>🏭 Domain Containers (Layer 3)</h2>
            <p style={{ margin: 0, opacity: 0.9, fontSize: '14px' }}>
              <strong>Swap this layer → New $B industry.</strong> Each container is a complete vertical solution. 
              Same 5 universal layers underneath. Customers see industry AI. You see one platform.
            </p>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', 
            gap: '20px' 
          }}>
            {domainContainers.map((container) => (
              <DomainContainerCard key={container.name} {...container} />
            ))}
          </div>

          {/* Revenue Calculator */}
          <div style={{ 
            marginTop: '32px',
            padding: '20px',
            background: 'white',
            borderRadius: '12px',
            border: '1px solid #e0e0e0'
          }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#333' }}>💰 Revenue Projection (Lego Tax Model)</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', fontSize: '12px' }}>
              <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                <div style={{ color: '#666' }}>Construction (50 customers)</div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#ff6b35' }}>$2,990/mo</div>
                <div style={{ color: '#999' }}>20% of $14,950</div>
              </div>
              <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                <div style={{ color: '#666' }}>Medical (30 customers)</div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#00b4d8' }}>$2,994/mo</div>
                <div style={{ color: '#999' }}>20% of $14,970</div>
              </div>
              <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                <div style={{ color: '#666' }}>Legal (40 customers)</div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#7b2cbf' }}>$3,192/mo</div>
                <div style={{ color: '#999' }}>20% of $15,960</div>
              </div>
              <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                <div style={{ color: '#666' }}>Finance (20 customers)</div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#2d6a4f' }}>$2,396/mo</div>
                <div style={{ color: '#999' }}>20% of $11,980</div>
              </div>
            </div>
            <div style={{ 
              marginTop: '16px', 
              padding: '16px', 
              background: '#1a1a2e', 
              color: 'white',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <span style={{ fontSize: '14px', opacity: 0.8 }}>Total Platform Revenue: </span>
              <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#00c853' }}>$11,572/mo</span>
              <span style={{ fontSize: '14px', opacity: 0.8 }}> = $138,864/year</span>
            </div>
          </div>
        </div>
      )}

      {/* Core AI Blocks Tab */}
      {activeTab === 'ai' && (
        <div>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '16px',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>🤖 Core AI Blocks (15)</h3>
            <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
              Building blocks used by all domain containers. Each block is self-contained and chainable.
            </p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>💬 Chat (DeepSeek)</div>
              <ChatBlock apiKey={API_KEY} provider="deepseek" maxHeight="250px" />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>🔍 Vector Search</div>
              <VectorBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>📄 PDF</div>
              <PDFBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>👁️ OCR</div>
              <OCRBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>🖼️ Image</div>
              <ImageBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>🔊 Voice</div>
              <VoiceBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>🕸️ Web</div>
              <WebBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>🔎 Search</div>
              <SearchBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>🌐 Translate</div>
              <TranslateBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>💻 Code</div>
              <CodeBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>🧮 Zvec</div>
              <ZvecBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>📬 Queue</div>
              <QueueBlock apiKey={API_KEY} jobId={activeJob || undefined} />
            </div>
          </div>
        </div>
      )}

      {/* Platform Services Tab */}
      {activeTab === 'platform' && (
        <div>
          <div style={{ 
            background: 'linear-gradient(135deg, #1a1a2e, #16213e)', 
            color: 'white',
            padding: '20px',
            borderRadius: '12px',
            marginBottom: '24px'
          }}>
            <h2 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>⚙️ Platform Services (Universal Layers)</h2>
            <p style={{ margin: 0, opacity: 0.9, fontSize: '13px' }}>
              These 3 containers (L1, L2, L4) never change. They power all domain verticals.
            </p>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(3, 1fr)', 
            gap: '20px',
            marginBottom: '24px'
          }}>
            {platformServices.map((service) => (
              <PlatformServiceCard key={service.name} {...service} />
            ))}
          </div>

          {/* Architecture Diagram */}
          <div style={{ 
            padding: '24px',
            background: 'white',
            borderRadius: '12px',
            border: '1px solid #e0e0e0'
          }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px' }}>🏗️ Domain Adapter Protocol Architecture</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {[
                { layer: 'Layer 5', name: 'Event Bus', color: '#ff006e', desc: 'Cross-container messaging' },
                { layer: 'Layer 4', name: 'Store', color: '#ff006e', desc: 'Marketplace, reviews, Lego Tax' },
                { layer: 'Layer 3', name: 'Domain Containers', color: '#ff6b35', desc: 'Construction, Medical, Legal, Finance...' },
                { layer: 'Layer 2', name: 'AI Core', color: '#0077b6', desc: 'Adaptive routing, failover, leaderboard' },
                { layer: 'Layer 1', name: 'Security', color: '#d00000', desc: 'Auth, rate limiting, sandbox, audit' },
                { layer: 'Layer 0', name: 'Infrastructure', color: '#6c757d', desc: 'HAL, memory, monitoring, config' },
              ].map((l) => (
                <div key={l.layer} style={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  padding: '12px 16px',
                  background: `${l.color}15`,
                  borderLeft: `4px solid ${l.color}`,
                  borderRadius: '4px'
                }}>
                  <span style={{ 
                    fontSize: '11px', 
                    fontWeight: 'bold',
                    color: l.color,
                    width: '70px'
                  }}>{l.layer}</span>
                  <span style={{ fontWeight: 'bold', width: '140px', color: '#333' }}>{l.name}</span>
                  <span style={{ fontSize: '12px', color: '#666' }}>{l.desc}</span>
                </div>
              ))}
            </div>
            <div style={{ 
              marginTop: '16px',
              padding: '12px',
              background: '#fff3cd',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#856404'
            }}>
              <strong>💡 Key Insight:</strong> Only Layer 3 changes per industry. Layers 0-2, 4-5 are universal. 
              This means 83% of the platform is reusable across every vertical.
            </div>
          </div>
        </div>
      )}

      {/* Infrastructure Tab */}
      {activeTab === 'infrastructure' && (
        <div>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '16px',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>🔧 Infrastructure (Layer 0)</h3>
            <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
              Foundation services that power the entire platform. HAL abstraction, memory cache, monitoring.
            </p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#1a1a2e', color: 'white', borderBottom: '1px solid #ddd' }}>🔧 HAL</div>
              <HALBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#1a1a2e', color: 'white', borderBottom: '1px solid #ddd' }}>🧠 Memory</div>
              <MemoryBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#1a1a2e', color: 'white', borderBottom: '1px solid #ddd' }}>📊 Monitoring</div>
              <MonitoringBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#1a1a2e', color: 'white', borderBottom: '1px solid #ddd' }}>🔐 Auth</div>
              <AuthBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#1a1a2e', color: 'white', borderBottom: '1px solid #ddd' }}>⚙️ Config</div>
              <ConfigBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#1a1a2e', color: 'white', borderBottom: '1px solid #ddd' }}>💰 Billing</div>
              <BillingBlock apiKey={API_KEY} />
            </div>
          </div>
        </div>
      )}

      {/* Storage Tab */}
      {activeTab === 'storage' && (
        <div>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '16px',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>💾 Storage & Integration</h3>
            <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
              Multi-drive support and integration blocks for external systems.
            </p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>💾 Storage</div>
              <StorageBlock apiKey={API_KEY} onFileSelect={setSelectedFile} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>📁 Google Drive</div>
              <GoogleDriveBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>☁️ OneDrive</div>
              <OneDriveBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>📱 Android Drive</div>
              <AndroidDriveBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>🗄️ Database</div>
              <DatabaseBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>📧 Email</div>
              <EmailBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>🎯 Webhook</div>
              <WebhookBlock apiKey={API_KEY} />
            </div>
            <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
              <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>⚡ Workflow</div>
              <WorkflowBlock apiKey={API_KEY} />
            </div>
          </div>
        </div>
      )}

      {/* Selected File Info */}
      {selectedFile && (
        <div style={{ 
          marginTop: '24px', 
          padding: '16px', 
          background: '#e3f2fd', 
          borderRadius: '8px',
          fontSize: '13px',
          border: '1px solid #90caf9'
        }}>
          <strong>📎 Selected File:</strong> {selectedFile.name} ({selectedFile.size} bytes)
        </div>
      )}

      {/* Footer */}
      <div style={{ 
        marginTop: '40px', 
        padding: '24px', 
        background: '#1a1a2e', 
        color: 'white',
        borderRadius: '12px',
        textAlign: 'center'
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>🚀 Build Your Own Domain Container</h3>
        <p style={{ margin: '0 0 16px 0', fontSize: '13px', opacity: 0.9 }}>
          Follow the Domain Container Specification to build and publish your own vertical. 
          Keep 80% of revenue. We handle the infrastructure.
        </p>
        <code style={{ 
          background: '#000', 
          padding: '8px 16px', 
          borderRadius: '4px',
          fontSize: '12px'
        }}>
          https://github.com/bopoadz-del/Cerebrum-Blocks/blob/main/DOMAIN_CONTAINER_SPEC.md
        </code>
      </div>
    </div>
  );
}

export default App;
