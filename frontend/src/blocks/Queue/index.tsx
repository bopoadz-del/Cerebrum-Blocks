// Queue-UI-Block - Background job monitoring
// <QueueBlock apiKey="cb_key" jobId="xxx" onComplete={(r) => console.log(r)} />

import { useState, useEffect } from 'react';
import { apiCall } from '../../api';

interface QueueBlockProps {
  apiKey: string;
  jobId?: string;
  onComplete?: (result: any) => void;
  pollInterval?: number; // ms
}

export const QueueBlock: React.FC<QueueBlockProps> = ({ 
  apiKey, 
  jobId,
  onComplete,
  pollInterval = 2000
}) => {
  const [status, setStatus] = useState<string>('idle');
  const [progress, setProgress] = useState<number>(0);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (!jobId) return;

    const checkStatus = async () => {
      try {
        const data = await apiCall('/v1/queue/status', { action: 'status', job_id: jobId });
        setStatus(data.status || 'unknown');
        
        // Get result if completed
        if (data.status === 'COMPLETED' || data.status === 'completed') {
          const resultData = await apiCall('/v1/queue/result', { action: 'result', job_id: jobId });
          setResult(resultData.result);
          onComplete?.(resultData.result);
        }
      } catch (error) {
        console.error('Queue status check failed:', error);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, pollInterval);
    
    return () => clearInterval(interval);
  }, [jobId]);

  if (!jobId) return null;

  return (
    <div className="queue-block" style={{ 
      padding: '10px', 
      background: '#f8f9fa', 
      borderRadius: '4px',
      border: '1px solid #ddd'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
        <span>Job: {jobId.substring(0, 8)}...</span>
        <span style={{ 
          color: status === 'COMPLETED' ? 'green' : status === 'FAILED' ? 'red' : 'orange',
          fontWeight: 'bold'
        }}>
          {status}
        </span>
      </div>
      
      {status === 'PROCESSING' && (
        <div style={{ 
          width: '100%', 
          height: '4px', 
          background: '#e9ecef',
          borderRadius: '2px',
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${progress}%`,
            height: '100%',
            background: '#007bff',
            transition: 'width 0.3s'
          }} />
        </div>
      )}
      
      {result && (
        <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
          ✅ Complete
        </div>
      )}
    </div>
  );
};
