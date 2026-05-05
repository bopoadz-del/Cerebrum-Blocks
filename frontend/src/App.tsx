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
  NextAction,
} from '@/types';
import { api, mapConstructionResult } from '@/api';
import { ThemeProvider } from '@/context/ThemeContext';
import LeftSidebar from '@/components/LeftSidebar';
import ChatArea from '@/components/ChatArea';
import RightPanel from '@/components/RightPanel';
import DriveConnectModal from '@/components/DriveConnectModal';
import ErrorBoundary from '@/components/ErrorBoundary';

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
  const [nextActions, setNextActions] = useState<NextAction[]>([]);
  const [activeChatContext, setActiveChatContext] = useState<string>('');

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

    const panels = analysisResult.panels || [];
    const qPanel = panels.find(p => p.type === 'quantities');
    const cPanel = panels.find(p => p.type === 'cost_estimate');
    const qPanelData = (qPanel?.data as Record<string, unknown> | undefined) || {};
    // Reference reads cPanel.line_items (panel-level) then falls back to inside data
    const cPanelData = cPanel?.data as { line_items?: unknown[]; items?: unknown[] } | undefined;
    const costLineItems: unknown[] = cPanel?.line_items || cPanelData?.line_items || cPanelData?.items || [];

    setActivePipelineCtx({
      file_path: filePath,
      extracted_text: extractedText,
      quantities: qPanelData,
      costLineItems,
      fileName,
    });
    setNextActions(analysisResult.next_actions || []);
    setActiveChatContext(analysisResult.chat_context || '');

    setRightOpen(true);
    return { ...mapped, chat_context: analysisResult.chat_context || '', fileName };
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
      // Track the freshest chat context — updated if a file is processed this turn
      let freshContext = activeChatContext;
      let freshFileName = activePipelineCtx?.fileName || '';

      if (files.length > 0) {
        for (const file of files) {
          const name = file.name.toLowerCase();
          const isPdf = file.type === 'application/pdf' || name.endsWith('.pdf');
          const isImage = file.type.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp|tiff)$/i.test(name);
          const isSpreadsheet = /\.(xls|xlsx)$/i.test(name);
          const isWord = /\.(doc|docx)$/i.test(name);
          const isText = file.type.startsWith('text/') || /\.(txt|md|csv)$/.test(name);

          if (isText) {
            const text = await file.text();
            addMessage('system', `Loaded "${file.name}":\n\n\`\`\`\n${text.slice(0, 2000)}${text.length > 2000 ? '\n...(truncated)' : ''}\n\`\`\``);
          } else if (isPdf || isImage || isSpreadsheet || isWord) {
            try {
              const pipelineResult = await runFilePipeline(file, null, file.name, isImage);
              freshContext = pipelineResult.chat_context;
              freshFileName = pipelineResult.fileName;
              addMessage('system', `Analyzed "${file.name}". Construction intelligence panels updated.`);
            } catch (err) {
              addMessage('error', `Failed to analyze "${file.name}": ${err instanceof Error ? err.message : 'Unknown error'}`);
            }
          } else {
            addMessage('system', `"${file.name}" (${(file.size / 1024).toFixed(1)} KB) — unsupported file type.`);
          }
        }
      }

      // Send text to chat API — works for text-only AND text+file (question about the file)
      if (content.trim()) {
        setProcessing({ active: true, stage: 'Generating response...', progress: 60 });
        const contextualContent = freshContext
          ? `I am asking about the file "${freshFileName}".\n\nContext:\n---\n${freshContext}\n---\n\nQuestion: ${content}`
          : content;
        const chatMessages = [...messages, { id: uuidv4(), role: 'user' as const, content: contextualContent, timestamp: Date.now() }];
        const result = await api.sendMessage(chatMessages);
        if (result.fallback) {
          const reason = result.fallback_reason === 'credit_exhausted'
            ? 'AI provider credits exhausted'
            : 'AI provider unavailable';
          addMessage('system', `⚠️ ${reason}. Showing rule-based fallback response.`);
        }
        addMessage('assistant', result.text || result.response || '');
      }
    } catch (err) {
      addMessage('error', err instanceof Error ? err.message : 'An unexpected error occurred.');
    } finally {
      setProcessing({ active: false, stage: '', progress: 0 });
    }
  }, [messages, addMessage, runFilePipeline, activeChatContext, activePipelineCtx]);

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
    setNextActions([]);
    setActiveChatContext('');
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
    const isSpreadsheet = /\.(xls|xlsx)$/.test(name);
    const isWord = /\.(doc|docx)$/.test(name);

    if (!isPdf && !isImage && !isSpreadsheet && !isWord) {
      addMessage('system', `"${fileNode.name}" is not a supported document type.`);
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

    // ZVec index file names for related-file search (fire-and-forget)
    const indexable = files.filter(f => /\.(pdf|txt|md|csv|docx)$/i.test(f.name)).slice(0, 200);
    if (indexable.length > 0) {
      api.runBlock('zvec', indexable.map(f => f.name).join('\n'), { operation: 'embed' }).catch(() => {});
    }

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

      // Procurement list generator — convert to ProcurementItem[] and show in panel
      if (action === 'procurement_list_generator') {
        const rawItems = result.procurement_list || result.items || [];
        if (rawItems.length > 0) {
          setProcurement(rawItems.map((item, i) => ({
            id: String(i + 1),
            item: item.item || item.name || 'Unknown',
            quantity: item.quantity || 0,
            unit: item.unit || 'units',
            leadTime: item.lead_time_weeks || item.lead_time_days || item.lead_time || 0,
            critical: item.priority === 'critical' || item.critical === true,
            supplier: item.supplier || undefined,
            status: item.status || 'PENDING',
          })));
        }
        const total = result.total_procurement_cost ? ` Total: $${Number(result.total_procurement_cost).toLocaleString()}.` : '';
        const critical = result.critical_long_lead_items ? ` ${result.critical_long_lead_items} critical long-lead items.` : '';
        addMessage('system', `Procurement list generated: ${rawItems.length} items.${total}${critical}`);

      // Actions that may return a panels array
      } else if (result.panels) {
        const mapped = mapConstructionResult(result);
        if (mapped.documentInfo) setDocumentInfo(mapped.documentInfo);
        if (mapped.quantities.length > 0) setQuantities(mapped.quantities);
        if (mapped.costEstimate) setCostEstimate(mapped.costEstimate);
        if (mapped.risks.length > 0) setRisks(mapped.risks);
        if (mapped.submittals.length > 0) setSubmittals(mapped.submittals);
        if (mapped.schedule.length > 0) setSchedule(mapped.schedule);
        if (mapped.contract.length > 0) setContract(mapped.contract);
        if (mapped.procurement.length > 0) setProcurement(mapped.procurement);
        addMessage('system', result.message || result.summary || result.chat_context || `${action.replace(/_/g, ' ')} complete.`);

      // Flat result — extract best available message
      } else {
        const summary =
          result.message ||
          result.summary ||
          result.text ||
          result.chat_context ||
          result.certificate_summary ||
          (result.overall_progress?.actual_percent != null ? `Overall progress: ${result.overall_progress.actual_percent}%` : null) ||
          JSON.stringify(result).slice(0, 300);
        addMessage('system', summary || `${action.replace(/_/g, ' ')} complete.`);
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
        accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.tiff,.txt,.md,.csv,.xls,.xlsx,.docx,.doc"
        className="hidden"
        onChange={handleLocalFilesSelected}
      />

      {/* Left Sidebar */}
      <ErrorBoundary label="Left sidebar">
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
      </ErrorBoundary>

      {/* Center Chat */}
      <div className="flex-1 min-w-0 rounded-2xl overflow-hidden">
        <ErrorBoundary label="Chat">
          <ChatArea
            messages={messages}
            onSendMessage={handleSendMessage}
            processing={processing}
            isLeftOpen={leftOpen}
            isRightOpen={rightOpen}
            onToggleLeft={() => setLeftOpen(!leftOpen)}
            onToggleRight={() => setRightOpen(!rightOpen)}
          />
        </ErrorBoundary>
      </div>

      {/* Right Panel */}
      <ErrorBoundary label="Right panel">
        <RightPanel
          documentInfo={documentInfo}
          quantities={quantities}
          costEstimate={costEstimate}
          risks={risks}
          submittals={submittals}
          schedule={schedule}
          contract={contract}
          procurement={procurement}
          nextActions={nextActions}
          onAction={handleAction}
          isOpen={rightOpen}
          onToggle={() => setRightOpen(!rightOpen)}
          width={rightWidth}
          onResize={setRightWidth}
        />
      </ErrorBoundary>

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
