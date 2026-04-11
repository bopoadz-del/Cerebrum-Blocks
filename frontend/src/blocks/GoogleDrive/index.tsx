// GoogleDrive-UI-Block
import { useState } from 'react';

interface GoogleDriveBlockProps {
  apiKey: string;
  onFileSelect?: (file: any) => void;
}

export const GoogleDriveBlock: React.FC<GoogleDriveBlockProps> = ({ apiKey, onFileSelect }) => {
  const [files, setFiles] = useState<any[]>([{ name: 'document.pdf' }, { name: 'image.jpg' }]);
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  return (
    <div style={{ padding: '10px', border: '1px solid #ddd', borderRadius: '4px' }}>
      <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd', marginBottom: '10px' }}>
        📁 Google Drive
      </div>
      {files.map((f, i) => (
        <div key={i} onClick={() => onFileSelect?.(f)} style={{ padding: '8px', cursor: 'pointer' }}>📄 {f.name}</div>
      ))}
    </div>
  );
};
