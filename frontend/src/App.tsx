import { Routes, Route, Navigate } from 'react-router';
import { ThemeProvider } from '@/context/ThemeContext';
import WorkflowBuilder from '@/pages/WorkflowBuilder';

function App() {
  return (
    <ThemeProvider>
      <Routes>
        <Route path="/" element={<WorkflowBuilder />} />
        <Route path="/builder" element={<Navigate to="/" replace />} />
      </Routes>
    </ThemeProvider>
  );
}

export default App;
