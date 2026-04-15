// Storage-UI-Block - File browser interface
// <StorageBlock apiKey="cb_key" onFileSelect={(f) => console.log(f)} />

import { useState, useEffect } from 'react';
import { API } from '../../api';

interface StorageBlockProps {
  apiKey: string;
  onFileSelect?: (file: any) => void;
  basePath?: string;
}

export const StorageBlock: React.FC<StorageBlockProps> = ({ 
  apiKey, 
  onFileSelect,
  basePath = ''
}) => {
  const [files, setFiles] = useState<any[]>([]);
  const [currentPath, setCurrentPath] = useState(basePath);
  const [loading, setLoading] = useState(false);

  const listFiles = async (path: string) => {
    setLoading(true);
    try {
      const data = await API.call('/v1/storage/list', { operation: 'list', path });
      setFiles(data.files || []);
      setCurrentPath(path);
    } catch (error) {
      console.error('Storage list failed:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    listFiles(currentPath);
  }, []);

  return (
    <div className="storage-block" style={{ border: '1px solid #ddd', borderRadius: '4px', minHeight: '300px' }}>
      <div className="storage-header" style={{ 
        padding: '10px', 
        background: '#f5f5f5', 
        borderBottom: '1px solid #ddd',
        display: 'flex',
        justifyContent: 'space-between'
      }}>
        <span>📁 {currentPath || '/'}</span>
        <button onClick={() => listFiles(currentPath)}>🔄</button>
      </div>
      
      <div className="storage-content" style={{ padding: '10px' }}>
        {loading ? (
          <div>Loading...</div>
        ) : (
          <>
            {currentPath !== '' && (
              <div 
                onClick={() => listFiles(currentPath.split('/').slice(0, -1).join('/'))}
                style={{ cursor: 'pointer', padding: '5px', color: '#666' }}
              >
                📁 ..
              </div>
            )}
            
            {files.map((file, idx) => (
              <div 
                key={idx}
                onClick={() => file.is_dir 
                  ? listFiles(`${currentPath}/${file.name}`)
                  : onFileSelect?.({ ...file, path: `${currentPath}/${file.name}` })
                }
                style={{ cursor: 'pointer', padding: '5px' }}
              >
                {file.is_dir ? '📁' : '📄'} {file.name}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
};
