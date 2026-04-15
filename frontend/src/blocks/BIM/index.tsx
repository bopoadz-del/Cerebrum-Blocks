// BIM-UI-Block - IFC model viewer and element browser
// <BIMBlock apiKey="cb_key" projectId="project_01" />

import { useState } from 'react';
import { API } from '../../api';

interface BIMBlockProps {
  apiKey: string;
  projectId: string;
  onElementSelect?: (element: any) => void;
}

export const BIMBlock: React.FC<BIMBlockProps> = ({ 
  apiKey, 
  projectId,
  onElementSelect
}) => {
  const [elements, setElements] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<any>(null);

  const loadIFC = async () => {
    setLoading(true);
    try {
      const data = await API.call('/v1/bim/load', { 
        action: 'load_ifc',
        project_id: projectId,
        ifc_path: `projects/${projectId}/model.ifc`
      });
      setElements(data.elements || []);
    } catch (error) {
      console.error('BIM load failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const queryElements = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await API.call('/v1/bim/query', { 
        action: 'query_elements',
        project_id: projectId,
        query
      });
      setElements(data.matches || []);
    } catch (error) {
      console.error('BIM query failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkProgress = async () => {
    try {
      const data = await API.call('/v1/bim/progress', { 
        action: 'get_progress',
        project_id: projectId,
        completed: []
      });
      setProgress(data);
    } catch (error) {
      console.error('Progress check failed:', error);
    }
  };

  return (
    <div className="bim-block" style={{ padding: '10px', border: '1px solid #ddd', borderRadius: '4px' }}>
      <div style={{ marginBottom: '10px', display: 'flex', gap: '10px' }}>
        <button onClick={loadIFC} disabled={loading} style={{ padding: '8px 16px' }}>
          📂 Load IFC
        </button>
        <button onClick={checkProgress} style={{ padding: '8px 16px' }}>
          📊 Progress
        </button>
      </div>

      {progress && (
        <div style={{ padding: '10px', background: '#f0f0f0', marginBottom: '10px', borderRadius: '4px' }}>
          <div>Progress: {progress.progress_percent}%</div>
          <div>Total: {progress.bim_elements_total} | Built: {progress.visually_detected}</div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && queryElements()}
          placeholder="Search BIM elements..."
          style={{ flex: 1, padding: '8px' }}
        />
        <button onClick={queryElements} disabled={loading}>
          {loading ? '...' : 'Search'}
        </button>
      </div>

      <div className="bim-elements" style={{ maxHeight: '300px', overflow: 'auto' }}>
        {elements.map((elem, idx) => (
          <div 
            key={idx}
            onClick={() => onElementSelect?.(elem)}
            style={{ 
              padding: '8px', 
              borderBottom: '1px solid #eee',
              cursor: 'pointer'
            }}
          >
            <strong>{elem.type || 'Element'}</strong>: {elem.name || elem}
          </div>
        ))}
      </div>
    </div>
  );
};
