// Monitoring-UI-Block - Provider Leaderboard & Health
// import { MonitoringBlock } from './blocks/Monitoring'
// <MonitoringBlock apiKey="cb_key" />

import { useState, useEffect } from 'react';
import { CerebrumClient } from '../../api/client';

interface MonitoringBlockProps {
  apiKey: string;
}

interface Provider {
  name: string;
  reliability_score: number;
  avg_latency_ms: number;
  success_rate: number;
  status: string;
  requests_24h: number;
}

interface SystemHealth {
  status: string;
  checks: Record<string, { status: string; latency_ms: number }>;
}

export const MonitoringBlock: React.FC<MonitoringBlockProps> = ({ apiKey }) => {
  const client = new CerebrumClient(apiKey);
  const [leaderboard, setLeaderboard] = useState<Provider[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [recommend, setRecommend] = useState<any>(null);
  const [predict, setPredict] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [lbData, healthData, recData, predData] = await Promise.all([
        client.leaderboard(),
        client.systemHealth(),
        client.recommend().catch(() => null),
        client.predict().catch(() => null)
      ]);
      setLeaderboard(lbData.leaderboard || []);
      setHealth(healthData);
      setRecommend(recData);
      setPredict(predData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch monitoring data');
      console.error('Failed to fetch monitoring data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [apiKey]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return '#28a745';
      case 'good': return '#17a2b8';
      case 'degraded': return '#ffc107';
      case 'failing': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getScoreWidth = (score: number) => {
    return `${Math.min(score, 100)}%`;
  };

  return (
    <div style={{ padding: '15px' }}>
      {error && (
        <div style={{ padding: '8px', background: '#f8d7da', borderRadius: '4px', fontSize: '12px', marginBottom: '10px' }}>
          {error}
        </div>
      )}

      {/* System Health */}
      {health && (
        <div style={{ marginBottom: '20px' }}>
          <h4 style={{ margin: '0 0 10px 0' }}>System Health
            <span style={{ 
              marginLeft: '10px',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px',
              background: health.status === 'healthy' ? '#28a745' : '#dc3545',
              color: 'white'
            }}>
              {health.status.toUpperCase()}
            </span>
          </h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {Object.entries(health.checks || {}).map(([name, check]) => (
              <div key={name} style={{
                padding: '6px 12px',
                borderRadius: '4px',
                fontSize: '11px',
                background: check.status === 'ok' ? '#d4edda' : '#f8d7da',
                color: check.status === 'ok' ? '#155724' : '#721c24',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}>
                <span>{check.status === 'ok' ? '✓' : '✗'}</span>
                {name}: {check.latency_ms}ms
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommend & Predict */}
      {(recommend || predict) && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '20px' }}>
          {recommend && (
            <div style={{ padding: '10px', background: '#e3f2fd', borderRadius: '4px', fontSize: '12px' }}>
              <strong>Recommend</strong>
              <pre style={{ margin: '5px 0 0 0', fontSize: '11px', overflow: 'auto', maxHeight: '80px' }}>
                {JSON.stringify(recommend, null, 2)}
              </pre>
            </div>
          )}
          {predict && (
            <div style={{ padding: '10px', background: '#f3e5f5', borderRadius: '4px', fontSize: '12px' }}>
              <strong>Predict</strong>
              <pre style={{ margin: '5px 0 0 0', fontSize: '11px', overflow: 'auto', maxHeight: '80px' }}>
                {JSON.stringify(predict, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Provider Leaderboard */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <h4 style={{ margin: 0 }}>Provider Leaderboard</h4>
          <button
            onClick={fetchData}
            disabled={loading}
            style={{
              padding: '4px 12px',
              background: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '11px'
            }}
          >
            {loading ? '...' : 'Refresh'}
          </button>
        </div>

        <div style={{ maxHeight: '250px', overflow: 'auto' }}>
          {leaderboard.length === 0 ? (
            <p style={{ color: '#6c757d', fontStyle: 'italic' }}>No provider data available</p>
          ) : (
            leaderboard.map((provider, idx) => (
              <div key={provider.name} style={{
                padding: '12px',
                borderBottom: '1px solid #eee',
                background: idx % 2 === 0 ? '#f8f9fa' : 'white'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      background: idx === 0 ? '#ffd700' : idx === 1 ? '#c0c0c0' : idx === 2 ? '#cd7f32' : '#e9ecef',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold',
                      fontSize: '12px'
                    }}>
                      {idx + 1}
                    </span>
                    <span style={{ fontWeight: 'bold' }}>{provider.name}</span>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '10px',
                      background: getStatusColor(provider.status),
                      color: 'white'
                    }}>
                      {provider.status}
                    </span>
                  </div>
                  <span style={{ fontSize: '12px', color: '#666' }}>
                    {provider.requests_24h?.toLocaleString()} req/24h
                  </span>
                </div>

                {/* Reliability Score Bar */}
                <div style={{ marginBottom: '5px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '2px' }}>
                    <span>Reliability</span>
                    <span>{provider.reliability_score.toFixed(1)}%</span>
                  </div>
                  <div style={{ height: '6px', background: '#e9ecef', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: getScoreWidth(provider.reliability_score),
                      background: getStatusColor(provider.status),
                      borderRadius: '3px',
                      transition: 'width 0.3s'
                    }} />
                  </div>
                </div>

                {/* Stats */}
                <div style={{ display: 'flex', gap: '20px', fontSize: '11px', color: '#666' }}>
                  <span>Latency: {provider.avg_latency_ms}ms</span>
                  <span>Success: {(provider.success_rate * 100).toFixed(1)}%</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* DeepSeek Highlight */}
      <div style={{ 
        marginTop: '15px', 
        padding: '10px', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '4px',
        color: 'white',
        fontSize: '12px'
      }}>
        <strong>🏆 Recommended: DeepSeek</strong>
        <div style={{ marginTop: '5px', opacity: 0.9 }}>
          $0.14/M tokens • 5x cheaper than GPT-3.5 • Best value for most tasks
        </div>
      </div>
    </div>
  );
};
