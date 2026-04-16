// Failover-UI-Block - System health dashboard
import { useState, useEffect } from 'react';
import { CerebrumClient } from '../../api/client';

interface FailoverBlockProps {
  apiKey: string;
}

export const FailoverBlock: React.FC<FailoverBlockProps> = ({ apiKey }) => {
  const client = new CerebrumClient(apiKey);
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await client.systemHealth();
        setStatus(data);
      } catch (e: any) {
        console.error('Failed to fetch status', e);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [apiKey]);

  if (!status) return <div>Loading...</div>;

  return (
    <div style={{ padding: '10px' }}>
      <div style={{ marginBottom: '10px', padding: '10px', background: '#f5f5f5', borderRadius: '4px' }}>
        <strong>System Health:</strong> {status.status}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px' }}>
        {Object.entries(status.blocks || {}).map(([name, block]: [string, any]) => (
          <div key={name} style={{ 
            padding: '8px', 
            background: block.status === 'healthy' ? '#e8f5e9' : '#ffebee',
            borderRadius: '4px',
            fontSize: '12px'
          }}>
            <strong>{name}</strong>: {block.status}
          </div>
        ))}
      </div>
    </div>
  );
};
