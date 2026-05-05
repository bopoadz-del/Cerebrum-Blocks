import { useState, useCallback, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import type {
  Message,
  Project,
  DriveSource,
  FileNode,
  DocumentInfo,
  QuantityItem,
  CostEstimate,
  Risk,
  Submittal,
  ScheduleItem,
  ContractClause,
  ProcurementItem,
  ProcessingState,
  PipelineCtx,
} from '@/types';
import { api, mapConstructionResult } from '@/api';
import { ThemeProvider } from '@/context/ThemeContext';
import LeftSidebar from '@/components/LeftSidebar';
import ChatArea from '@/components/ChatArea';
import RightPanel from '@/components/RightPanel';
import DriveConnectModal from '@/components/DriveConnectModal';

function AppContent() {
  // Panel layout state
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const [leftWidth, setLeftWidth] = useState(280);
  const [rightWidth, setRightWidth] = useState(320);

  // Data state — start empty, populated from real API calls only
  const [projects, setProjects] = useState<Project[]>([]);
  const [drives, setDrives] = useState<DriveSource[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [processing, setProcessing] = useState<ProcessingState>({ active: false, stage: '', progress: 0 });
  const [showDriveModal, setShowDriveModal] = useState(false);

  // Construction panel results
  const [documentInfo, setDocumentInfo] = useState<DocumentInfo | null>(null);
  const [quantities, setQuantities] = useState<QuantityItem[]>([]);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [submittals, setSubmittals] = useState<Submittal[]>([]);
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
  const [contract, setContract] = useState<ContractClause[]>([]);
  const [procurement, setProcurement] = useState<ProcurementItem[]>([]);

  // Active pipeline context — stored after successful analysis, used by action buttons
  const [activePipelineCtx, setActivePipelineCtx] = useState<PipelineCtx | null>(null);

  // Hidden file input for local drive browsing
  const localFileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.health().catch(() => {
      console.log('API health check failed — server may be waking up');
    });
  }, []);

  const addMessage = useCallback((role: Message['role'], content: string, attachments?: Message['attachments']) => {
    const message: Message = {
      id: uuidv4(),
      role,
      content,
      timestamp: Date.now(),
      attachments,
    };
    setMessages(prev => [...prev, message]);
    return message;
  }, []);

  // Run the 3-step pipeline for a file and update all panels + pipeline context
  const runFilePipeline = useCallback(async (
    file: File | null,
    serverPath: string | null,
    fileName: string,
    isImage: boolean
  ) => {
    let filePath: string;

    setProcessing({ active: true, stage: 'Uploading document...', progress: 15 });

    if (file) {
      const uploadResult = await api.uploadFile(file);
      filePath = uploadResult.file_path;
    } else if (serverPath) {
      filePath = serverPath;
    } else {
      throw new Error('No file or server path provided');
    }

    setProcessing({ active: true, stage: 'Extracting text...', progress: 40 });
    const extractedText = await api.extractText(filePath, isImage).catch(() => '');

    setProcessing({ active: true, stage: 'Running construction analysis...', progress: 65 });
    const analysisResult = await api.analyzeConstruction(filePath, extractedText);
    const mapped = mapConstructionResult(analysisResult);

    setDocumentInfo(mapped.documentInfo);
    setQuantities(mapped.quantities);
    setCostEstimate(mapped.costEstimate);
    setRisks(mapped.risks);
    setSubmittals(mapped.submittals);
    setSchedule(mapped.schedule);
    setContract(mapped.contract);
    setProcurement(mapped.procurement);

    const panels: any[] = analysisResult.panels || [];
    const qPanelData = panels.find((p: any) => p.type === 'quantities')?.data || {};
    const cPanelData = panels.find((p: any) => p.type === 'cost_estimate')?.data || {};

    setActivePipelineCtx({
      file_path: filePath,
      extracted_text: extractedText,
      quantities: qPanelData,
      costLineItems: cPanelData.line_items || cPanelData.items || [],
      fileName,
    });

    setRightOpen(true);
    return mapped;
  }, []);

  const handleSendMessage = useCallback(async (content: string, files: File[]) => {
    const attachments: Message['attachments'] = files.map(f => ({
      name: f.name,
      type: f.type,
      size: f.size,
    }));
    addMessage('user', content || `Uploaded ${files.length} file(s)`, attachments.length ? attachments : undefined);

    setProcessing({ active: true, stage: 'Processing...', progress: 0 });

    try {
      if (files.length > 0) {
        for (const file of files) {
          const name = file.name.toLowerCase();
          const isPdf = file.type === 'application/pdf' || name.endsWith('.pdf');
          const isImage = file.type.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp|tiff)$/i.test(name);
          const isText = file.type.startsWith('text/') || /\.(txt|md|csv)$/.test(name);

          if (isText) {
            const text = await file.text();
            addMessage('system', `Loaded "${file.name}":\n\n\`\`\`\n${text.slice(0, 2000)}${text.length > 2000 ? '\n...(truncated)' : ''}\n\`\`\``);
          } else if (isPdf || isImage) {
            try {
              await runFilePipeline(file, null, file.name, isImage);
              addMessage('system', `Analyzed "${file.name}". Construction intelligence panels updated.`);
            } catch (err) {
              addMessage('error', `Failed to analyze "${file.name}": ${err instanceof Error ? err.message : 'Unknown error'}`);
            }
          } else {
            addMessage('system', `"${file.name}" (${(file.size / 1024).toFixed(1)} KB) — binary file, cannot be analyzed directly.`);
          }
        }
      }

      // Text-only message → chat API
      if (content.trim() && files.length === 0) {
        setProcessing({ active: true, stage: 'Generating response...', progress: 60 });
        const result = await api.sendMessage([...messages, { id: uuidv4(), role: 'user', content, timestamp: Date.now() }]);
        addMessage('assistant', result.text || result.response || '');
      }
    } catch (err) {
      addMessage('error', err instanceof Error ? err.message : 'An unexpected error occurred.');
    } finally {
      setProcessing({ active: false, stage: '', progress: 0 });
    }
  }, [messages, addMessage, runFilePipeline]);

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setDocumentInfo(null);
    setQuantities([]);
    setCostEstimate(null);
    setRisks([]);
    setSubmittals([]);
    setSchedule([]);
    setContract([]);
    setProcurement([]);
    setActivePipelineCtx(null);
  }, []);

  const handleSelectProject = useCallback((project: Project) => {
    setProjects(prev => prev.map(p => ({ ...p, active: p.id === project.id })));
    addMessage('system', `Switched to project: ${project.name}`);
  }, [addMessage]);

  const handleSelectFile = useCallback(async (fileNode: FileNode, drive: DriveSource) => {
    if (fileNode.type === 'folder') return;

    const name = fileNode.name.toLowerCase();
    const isPdf = name.endsWith('.pdf');
    const isImage = /\.(jpg|jpeg|png|gif|webp|tiff)$/.test(name);

    if (!isPdf && !isImage) {
      addMessage('system', `"${fileNode.name}" is not a supported document type (PDF or image required).`);
      return;
    }

    setProcessing({ active: true, stage: 'Loading file...', progress: 5 });

    try {
      if (drive.type === 'local') {
        const fileObj = drive.fileObjects?.find(f => f.name === fileNode.name);
        if (!fileObj) {
          addMessage('system', `File object for "${fileNode.name}" not found. Please re-select your local files.`);
          setProcessing({ active: false, stage: '', progress: 0 });
          return;
        }
        await runFilePipeline(fileObj, null, fileNode.name, isImage);
      } else {
        const serverPath = fileNode.path || fileNode.name;
        await runFilePipeline(null, serverPath, fileNode.name, isImage);
      }
      addMessage('system', `Analyzed "${fileNode.name}" from ${drive.name}. Construction intelligence panels updated.`);
    } catch (err) {
      addMessage('error', `Failed to analyze "${fileNode.name}": ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setProcessing({ active: false, stage: '', progress: 0 });
    }
  }, [addMessage, runFilePipeline]);

  // Called when local file input fires
  const handleLocalFilesSelected = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    const fileNodes: FileNode[] = files.map(f => ({
      id: uuidv4(),
      name: f.name,
      type: 'file' as const,
      path: f.name,
    }));

    const newDrive: DriveSource = {
      id: 'local-1',
      name: 'My Device',
      icon: 'hard-drive',
      connected: true,
      type: 'local',
      files: fileNodes,
      fileObjects: files,
    };

    setDrives(prev => {
      const idx = prev.findIndex(d => d.type === 'local');
      if (idx >= 0) {
        const updated = [...prev];
        updated[idx] = newDrive;
        return updated;
      }
      return [...prev, newDrive];
    });

    // Reset so the same files can be re-selected
    event.target.value = '';
  }, []);

  const handleBrowseLocal = useCallback(() => {
    localFileInputRef.current?.click();
  }, []);

  const handleConnectDrive = useCallback((drive: DriveSource) => {
    setDrives(prev => {
      const idx = prev.findIndex(d => d.type === drive.type);
      if (idx >= 0) {
        const updated = [...prev];
        updated[idx] = { ...updated[idx], connected: true, files: drive.files || updated[idx].files };
        return updated;
      }
      return [...prev, drive];
    });
  }, []);

  const handleAction = useCallback(async (action: string) => {
    if (!activePipelineCtx) {
      addMessage('system', 'No document loaded. Upload and analyze a document first.');
      return;
    }

    addMessage('system', `Running ${action.replace(/_/g, ' ')}...`);
    setProcessing({ active: true, stage: `Running ${action}...`, progress: 30 });

    try {
      const result = await api.runAction(action, activePipelineCtx);
      const summary =
        result.message ||
        result.summary ||
        result.text ||
        result.chat_context ||
        (result.panels ? `${result.panels.length} panel(s) updated.` : JSON.stringify(result).slice(0, 300));
      addMessage('system', summary);

      // If the action returned panels, refresh the display
      if (result.panels) {
        const mapped = mapConstructionResult(result);
        if (mapped.documentInfo) setDocumentInfo(mapped.documentInfo);
        if (mapped.quantities.length > 0) setQuantities(mapped.quantities);
        if (mapped.costEstimate) setCostEstimate(mapped.costEstimate);
        if (mapped.risks.length > 0) setRisks(mapped.risks);
        if (mapped.submittals.length > 0) setSubmittals(mapped.submittals);
        if (mapped.schedule.length > 0) setSchedule(mapped.schedule);
        if (mapped.contract.length > 0) setContract(mapped.contract);
        if (mapped.procurement.length > 0) setProcurement(mapped.procurement);
      }
    } catch (err) {
      addMessage('error', `Action "${action}" failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setProcessing({ active: false, stage: '', progress: 0 });
    }
  }, [activePipelineCtx, addMessage]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[hsl(var(--background))] text-[hsl(var(--foreground))] p-2 gap-2">
      {/* Hidden file input for local drive */}
      <input
        ref={localFileInputRef}
        type="file"
        multiple
        accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.tiff,.txt,.md,.csv"
        className="hidden"
        onChange={handleLocalFilesSelected}
      />

      {/* Left Sidebar */}
      <LeftSidebar
        projects={projects}
        drives={drives}
        onNewChat={handleNewChat}
        onConnectDrive={() => setShowDriveModal(true)}
        onSelectProject={handleSelectProject}
        onSelectFile={handleSelectFile}
        isOpen={leftOpen}
        onToggle={() => setLeftOpen(!leftOpen)}
        width={leftWidth}
        onResize={setLeftWidth}
      />

      {/* Center Chat */}
      <div className="flex-1 min-w-0 rounded-2xl overflow-hidden">
        <ChatArea
          messages={messages}
          onSendMessage={handleSendMessage}
          processing={processing}
          isLeftOpen={leftOpen}
          isRightOpen={rightOpen}
          onToggleLeft={() => setLeftOpen(!leftOpen)}
          onToggleRight={() => setRightOpen(!rightOpen)}
        />
      </div>

      {/* Right Panel */}
      <RightPanel
        documentInfo={documentInfo}
        quantities={quantities}
        costEstimate={costEstimate}
        risks={risks}
        submittals={submittals}
        schedule={schedule}
        contract={contract}
        procurement={procurement}
        onAction={handleAction}
        isOpen={rightOpen}
        onToggle={() => setRightOpen(!rightOpen)}
        width={rightWidth}
        onResize={setRightWidth}
      />

      {/* Drive Connect Modal */}
      <DriveConnectModal
        isOpen={showDriveModal}
        onClose={() => setShowDriveModal(false)}
        onConnect={handleConnectDrive}
        onBrowseLocal={handleBrowseLocal}
        existingDrives={drives}
      />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
