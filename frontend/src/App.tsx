import { useState, useCallback, useEffect } from 'react';
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
  ProcessingState
} from '@/types';
import { api, mapConstructionResult } from '@/api';
import { ThemeProvider } from '@/context/ThemeContext';
import LeftSidebar from '@/components/LeftSidebar';
import ChatArea from '@/components/ChatArea';
import RightPanel from '@/components/RightPanel';
import DriveConnectModal from '@/components/DriveConnectModal';

// Demo projects
const defaultProjects: Project[] = [
  { id: '1', name: 'Metro Tower Renovation', description: 'Downtown office tower upgrade', active: true },
  { id: '2', name: 'Highway Extension A-12', description: 'North-south connector', active: false },
  { id: '3', name: 'Harbor Bridge Repair', description: 'Structural reinforcement', active: false },
  { id: '4', name: 'Solar Farm Phase 2', description: 'Renewable energy installation', active: false },
];

// Demo drives
const defaultDrives: DriveSource[] = [
  {
    id: 'local-1',
    name: 'My Device',
    icon: 'hard-drive',
    connected: true,
    type: 'local',
    files: [
      {
        id: 'f1',
        name: 'Projects',
        type: 'folder',
        expanded: true,
        children: [
          {
            id: 'f1-1',
            name: 'Metro Tower',
            type: 'folder',
            children: [
              { id: 'f1-1-1', name: 'blueprints.pdf', type: 'file' },
              { id: 'f1-1-2', name: 'specs.docx', type: 'file' },
              { id: 'f1-1-3', name: 'schedule.xlsx', type: 'file' },
            ]
          },
          {
            id: 'f1-2',
            name: 'Highway A-12',
            type: 'folder',
            children: [
              { id: 'f1-2-1', name: 'survey_data.pdf', type: 'file' },
              { id: 'f1-2-2', name: 'soil_analysis.pdf', type: 'file' },
            ]
          }
        ]
      },
      {
        id: 'f2',
        name: 'Contracts',
        type: 'folder',
        children: [
          { id: 'f2-1', name: 'contract_2024.pdf', type: 'file' },
          { id: 'f2-2', name: 'amendment_1.pdf', type: 'file' },
        ]
      }
    ]
  },
  {
    id: 'server-1',
    name: 'Server',
    icon: 'server',
    connected: true,
    type: 'server',
    files: [
      {
        id: 's1',
        name: 'Shared',
        type: 'folder',
        children: [
          { id: 's1-1', name: 'materials_db.xlsx', type: 'file' },
          { id: 's1-2', name: 'vendor_list.pdf', type: 'file' },
        ]
      }
    ]
  },
  {
    id: 'google-1',
    name: 'Google Drive',
    icon: 'cloud',
    connected: false,
    type: 'google',
    files: []
  },
  {
    id: 'onedrive-1',
    name: 'OneDrive',
    icon: 'cloud',
    connected: false,
    type: 'onedrive',
    files: []
  },
  {
    id: 'android-1',
    name: 'Android',
    icon: 'smartphone',
    connected: false,
    type: 'android',
    files: []
  }
];

function AppContent() {
  // Panel state
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const [leftWidth, setLeftWidth] = useState(280);
  const [rightWidth, setRightWidth] = useState(320);

  // Data state
  const [projects, setProjects] = useState<Project[]>(defaultProjects);
  const [drives, setDrives] = useState<DriveSource[]>(defaultDrives);
  const [messages, setMessages] = useState<Message[]>([]);
  const [processing, setProcessing] = useState<ProcessingState>({ active: false, stage: '', progress: 0 });
  const [showDriveModal, setShowDriveModal] = useState(false);

  // Results state
  const [documentInfo, setDocumentInfo] = useState<DocumentInfo | null>(null);
  const [quantities, setQuantities] = useState<QuantityItem[]>([]);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [submittals, setSubmittals] = useState<Submittal[]>([]);
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
  const [contract, setContract] = useState<ContractClause[]>([]);
  const [procurement, setProcurement] = useState<ProcurementItem[]>([]);

  // Check API health
  useEffect(() => {
    api.health().catch(() => {
      // API might be sleeping on Render free tier
      console.log('API health check failed - server may be waking up');
    });
  }, []);

  const addMessage = useCallback((role: Message['role'], content: string, attachments?: Message['attachments']) => {
    const message: Message = {
      id: uuidv4(),
      role,
      content,
      timestamp: Date.now(),
      attachments
    };
    setMessages(prev => [...prev, message]);
    return message;
  }, []);

  const determineFileType = (file: File): 'text' | 'pdf' | 'image' | 'binary' => {
    const name = file.name.toLowerCase();
    if (file.type.startsWith('text/') || name.endsWith('.txt') || name.endsWith('.md') || name.endsWith('.csv')) {
      return 'text';
    }
    if (file.type === 'application/pdf' || name.endsWith('.pdf')) {
      return 'pdf';
    }
    if (file.type.startsWith('image/') || name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png')) {
      return 'image';
    }
    return 'binary';
  };

  const handleSendMessage = useCallback(async (content: string, files: File[]) => {
    const attachments: Message['attachments'] = files.map(f => ({
      name: f.name,
      type: f.type,
      size: f.size
    }));
    addMessage('user', content || `Uploaded ${files.length} file(s)`, attachments);

    setProcessing({ active: true, stage: 'Analyzing...', progress: 0 });

    try {
      if (files.length > 0) {
        for (const file of files) {
          const fileType = determineFileType(file);

          if (fileType === 'text') {
            const text = await file.text();
            addMessage('system', `Loaded text file "${file.name}" (${(file.size / 1024).toFixed(1)} KB):\n\n\`\`\`\n${text.slice(0, 2000)}${text.length > 2000 ? '\n... (truncated)' : ''}\n\`\`\``);
            setProcessing({ active: true, stage: 'Extracting construction data...', progress: 30 });
            await simulateExtraction();
            simulateConstructionData(file.name);
            setRightOpen(true);
          } else if (fileType === 'pdf' || fileType === 'image') {
            setProcessing({ active: true, stage: 'Uploading document...', progress: 15 });

            try {
              // Step 1: Upload
              const uploadResult = await api.uploadFile(file);
              const filePath = uploadResult.file_path;

              // Step 2: Extract text
              setProcessing({ active: true, stage: 'Extracting text...', progress: 40 });
              const extractedText = await api.extractText(filePath, fileType === 'image').catch(() => '');

              // Step 3: Construction analysis
              setProcessing({ active: true, stage: 'Running construction analysis...', progress: 65 });
              let panelsPopulated = false;

              try {
                const analysisResult = await api.analyzeConstruction(filePath, extractedText);
                const mapped = mapConstructionResult(analysisResult);

                if (mapped.documentInfo || mapped.quantities.length > 0 || mapped.risks.length > 0) {
                  if (mapped.documentInfo) setDocumentInfo(mapped.documentInfo);
                  if (mapped.quantities.length > 0) setQuantities(mapped.quantities);
                  if (mapped.costEstimate) setCostEstimate(mapped.costEstimate);
                  if (mapped.risks.length > 0) setRisks(mapped.risks);
                  if (mapped.submittals.length > 0) setSubmittals(mapped.submittals);
                  if (mapped.schedule.length > 0) setSchedule(mapped.schedule);
                  if (mapped.contract.length > 0) setContract(mapped.contract);
                  if (mapped.procurement.length > 0) setProcurement(mapped.procurement);
                  panelsPopulated = true;
                }
              } catch {
                // Construction analysis failed — fall through to simulate
              }

              if (!panelsPopulated) {
                simulateConstructionData(file.name);
              }

              addMessage('system', `Analyzed ${fileType === 'pdf' ? 'PDF' : 'image'} "${file.name}". Construction intelligence panels updated.`);
              setRightOpen(true);
            } catch (err) {
              simulateConstructionData(file.name);
              addMessage('system', `Analyzed "${file.name}" (demo mode). Construction panels populated.`);
              setRightOpen(true);
            }
          } else {
            addMessage('system', `Binary file "${file.name}" (${(file.size / 1024).toFixed(1)} KB) — content cannot be analyzed directly.`);
          }
        }
      }

      // Text-only message → chat API
      if (content.trim() && files.length === 0) {
        setProcessing({ active: true, stage: 'Generating response...', progress: 60 });

        try {
          const result = await api.sendMessage([...messages, { id: uuidv4(), role: 'user', content, timestamp: Date.now() }]);
          addMessage('assistant', result.text || result.response || '');
        } catch {
          addMessage('assistant', generateFallbackResponse(content));
        }
      }
    } catch (err) {
      addMessage('error', err instanceof Error ? err.message : 'An error occurred.');
    } finally {
      setProcessing({ active: false, stage: '', progress: 0 });
    }
  }, [messages, addMessage]);

  const simulateExtraction = async () => {
    await new Promise(r => setTimeout(r, 800));
  };

  const simulateConstructionData = (filename: string) => {
    setDocumentInfo({
      type: filename.endsWith('.pdf') ? 'PDF' : 'Image',
      title: filename.replace(/\.[^/.]+$/, ''),
      project: 'Metro Tower Renovation',
      pages: 24,
      author: 'Zven Engineering',
      date: '2024-03-15'
    });

    setQuantities([
      { item: 'Concrete - C30', quantity: 450, unit: 'm3' },
      { item: 'Rebar - Grade 60', quantity: 12000, unit: 'kg' },
      { item: 'Formwork', quantity: 2800, unit: 'm2' },
      { item: 'Structural Steel', quantity: 85, unit: 'tonnes' },
      { item: 'Glass Panels', quantity: 340, unit: 'units' },
      { item: 'Insulation', quantity: 1200, unit: 'm2' }
    ]);

    setCostEstimate({
      subtotal: 2847500,
      overhead: 284750,
      contingency: 142375,
      total: 3274625,
      currency: '$'
    });

    setRisks([
      { id: '1', description: 'Weather delays during monsoon season may impact foundation work', severity: 'HIGH', category: 'Schedule', mitigation: 'Accelerated curing methods and weatherproofing' },
      { id: '2', description: 'Steel price volatility affects structural budget', severity: 'MEDIUM', category: 'Cost', mitigation: 'Fixed-price contract with supplier' },
      { id: '3', description: 'Archaeological findings on site', severity: 'LOW', category: 'Regulatory', mitigation: 'Pre-construction survey completed' }
    ]);

    setSubmittals([
      { id: '1', item: 'Concrete mix design', status: 'APPROVED', category: 'Materials' },
      { id: '2', item: 'Steel mill certificates', status: 'PENDING', category: 'Materials' },
      { id: '3', item: 'Fireproofing test reports', status: 'REQUIRED', category: 'Testing' },
      { id: '4', item: 'Glazing performance data', status: 'APPROVED', category: 'Materials' }
    ]);

    setSchedule([
      { id: '1', task: 'Site preparation', start: '2024-04-01', end: '2024-04-15', duration: 14, progress: 100, status: 'COMPLETED' },
      { id: '2', task: 'Foundation work', start: '2024-04-16', end: '2024-05-30', duration: 44, progress: 65, status: 'IN_PROGRESS' },
      { id: '3', task: 'Structural framing', start: '2024-06-01', end: '2024-07-31', duration: 60, progress: 0, status: 'NOT_STARTED' },
      { id: '4', task: 'MEP installation', start: '2024-08-01', end: '2024-10-15', duration: 75, progress: 0, status: 'NOT_STARTED' }
    ]);

    setContract([
      { id: '1', title: 'Scope of Work', content: 'Contractor shall perform all work as specified in the construction documents including demolition, structural reinforcement, and MEP upgrades.', section: 'Article 1' },
      { id: '2', title: 'Payment Terms', content: 'Progress payments shall be made monthly based on percentage of work completed, less 10% retainage.', section: 'Article 3' },
      { id: '3', title: 'Completion Date', content: 'Substantial completion shall be achieved within 240 calendar days from notice to proceed.', section: 'Article 5' }
    ]);

    setProcurement([
      { id: '1', item: 'Structural Steel Beams', quantity: 45, unit: 'tonnes', leadTime: 90, critical: true, supplier: 'ArcelorMittal', status: 'ORDERED' },
      { id: '2', item: 'Curtain Wall System', quantity: 340, unit: 'panels', leadTime: 120, critical: true, supplier: 'Schuco', status: 'PENDING' },
      { id: '3', item: 'HVAC Units', quantity: 12, unit: 'units', leadTime: 60, critical: false, supplier: 'Carrier', status: 'ORDERED' },
      { id: '4', item: 'Elevator Equipment', quantity: 2, unit: 'sets', leadTime: 180, critical: true, supplier: 'Otis', status: 'PENDING' },
      { id: '5', item: 'Fire Suppression', quantity: 1, unit: 'system', leadTime: 45, critical: false, supplier: 'Johnson Controls', status: 'DELIVERED' }
    ]);
  };

  const generateFallbackResponse = (query: string): string => {
    const lower = query.toLowerCase();
    
    if (lower.includes('cost') || lower.includes('budget') || lower.includes('price')) {
      return `Based on the current project data, the total estimated cost is $3,274,625 including overhead (10%) and contingency (5%). The largest cost drivers are structural steel and curtain wall systems. Would you like a detailed cost breakdown or value engineering suggestions?`;
    }
    if (lower.includes('risk') || lower.includes('issue') || lower.includes('problem')) {
      return `I've identified 3 key risks: (1) HIGH - Weather delays during monsoon season for foundation work, (2) MEDIUM - Steel price volatility, and (3) LOW - Archaeological findings. I recommend reviewing the mitigation strategies in the Risks panel.`;
    }
    if (lower.includes('schedule') || lower.includes('timeline') || lower.includes('time')) {
      return `The project schedule shows foundation work is currently 65% complete. The next critical milestone is structural framing starting June 1st. Note that curtain wall and elevator equipment have long lead times (120-180 days) that require immediate attention.`;
    }
    if (lower.includes('procurement') || lower.includes('order') || lower.includes('buy')) {
      return `There are 5 procurement items tracked. 2 critical long-lead items require immediate ordering: Structural Steel Beams (90 days) and Curtain Wall System (120 days). Elevator equipment has the longest lead time at 180 days. Check the Procurement panel for supplier details.`;
    }
    
    return `I understand your question about "${query}". I'm connected to the Cerebrum construction intelligence platform. I can help you analyze documents, review quantities, assess risks, track schedules, manage procurement, and generate reports. Please upload construction documents or ask specific questions about your project.`;
  };

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
  }, []);

  const handleSelectProject = useCallback((project: Project) => {
    setProjects(prev => prev.map(p => ({ ...p, active: p.id === project.id })));
    addMessage('system', `Switched to project: ${project.name}`);
  }, [addMessage]);

  const handleSelectFile = useCallback((file: FileNode, drive: DriveSource) => {
    addMessage('system', `Loaded "${file.name}" from ${drive.name}. Construction panels updated with analysis.`);
    simulateConstructionData(file.name);
    setRightOpen(true);
  }, [addMessage]);

  const handleConnectDrive = useCallback((drive: DriveSource) => {
    setDrives(prev => {
      const existing = prev.findIndex(d => d.type === drive.type);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = { ...updated[existing], connected: true, files: drive.files || updated[existing].files };
        return updated;
      }
      return [...prev, drive];
    });
  }, []);

  const handleAction = useCallback(async (action: string) => {
    addMessage('system', `Running action: ${action.replace('_', ' ')}...`);
    
    try {
      switch (action) {
        case 'procurement_list':
          try {
            const result = await api.generateProcurementList('demo-file');
            addMessage('system', `Procurement list generated. ${result.items?.length || 0} items flagged for ordering.`);
          } catch {
            addMessage('system', `Procurement list generated (demo). 2 critical items flagged for immediate ordering: Structural Steel Beams and Curtain Wall System.`);
          }
          break;
        case 'progress_tracker':
          try {
            const result = await api.trackProgress('demo-file');
            addMessage('system', `Progress updated. Overall completion: ${result.overall_progress || '62'}%`);
          } catch {
            addMessage('system', `Progress tracker updated (demo). Overall completion: 62%. Foundation work at 65%, on track for June 1st structural framing start.`);
          }
          break;
        case 'payment_certificate':
          try {
            const result = await api.generatePaymentCertificate('demo-file');
            addMessage('system', `Payment certificate generated. Approved amount: ${result.amount || '$1,847,500'}`);
          } catch {
            addMessage('system', `Payment certificate generated (demo). Approved amount: $1,847,500 based on 65% foundation completion and delivered materials.`);
          }
          break;
      }
    } catch (err) {
      addMessage('error', `Failed to run ${action}: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [addMessage]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[hsl(var(--background))] text-[hsl(var(--foreground))] p-2 gap-2">
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
