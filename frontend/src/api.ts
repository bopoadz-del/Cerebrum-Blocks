import type {
  Message,
  DocumentInfo,
  QuantityItem,
  CostEstimate,
  Risk,
  Submittal,
  ScheduleItem,
  ContractClause,
  ProcurementItem,
  PipelineCtx,
  FileNode,
  RawPanel,
  RawRisk,
  RawSubmittal,
  RawScheduleActivity,
  RawContractClause,
  RawProcurementItem,
  RawDriveFile,
  ConstructionApiResult,
} from '@/types';

const isLocalHost =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

const API_BASE =
  import.meta.env.VITE_API_BASE ??
  (isLocalHost ? 'http://localhost:8000' : 'https://cerebrum-platform-api.onrender.com');

// Public-tier key injected at build time. SPAs cannot keep secrets — this key
// must be scoped to client-safe operations on the server. Never inline a master key.
const API_KEY = import.meta.env.VITE_API_KEY ?? (isLocalHost ? 'cb_dev_key' : '');

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function fetchApi(path: string, options?: RequestInit): Promise<unknown> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error || `HTTP ${response.status}`);
  }

  return response.json();
}

// Unwrap the optional `{ result: ... }` envelope some endpoints use.
function unwrapResult<T = ConstructionApiResult>(raw: unknown): T {
  const r = raw as { result?: T } | T;
  return ((r as { result?: T })?.result ?? r) as T;
}

export const api = {
  // Chat — sends last message with up to 6 prior turns for multi-turn context
  async sendMessage(messages: Message[]): Promise<{ text: string; response?: string }> {
    const lastUser = [...messages].reverse().find(m => m.role === 'user');
    if (!lastUser) return { text: '' };

    // Build conversation history from prior turns (exclude the current message)
    const priorTurns = messages
      .filter(m => m.id !== lastUser.id && (m.role === 'user' || m.role === 'assistant'))
      .slice(-6);

    let message = lastUser.content || '';
    if (priorTurns.length > 0) {
      const historyText = priorTurns
        .map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`)
        .join('\n');
      message = `Previous conversation:\n${historyText}\n\nCurrent message: ${message}`;
    }

    return fetchApi('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, model: 'deepseek-chat', stream: false }),
    }) as Promise<{ text: string; response?: string }>;
  },

  // Upload — multipart; returns file_path (absolute server path)
  async uploadFile(file: File): Promise<{ file_path: string; filename: string; url: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${API_KEY}` },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new ApiError(response.status, error);
    }

    return response.json();
  },

  // Extract text from a PDF or image via the pdf/ocr block
  async extractText(filePath: string, isImage = false): Promise<string> {
    const block = isImage ? 'ocr' : 'pdf';
    const raw = await fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        block,
        input: { file_path: filePath },
        params: {},
      }),
    });
    const inner = unwrapResult<{ text?: string; content?: string }>(raw);
    return inner.text || inner.content || '';
  },

  // Run construction auto_pipeline — action must be in params, NOT in input
  async analyzeConstruction(filePath: string, extractedText: string): Promise<ConstructionApiResult> {
    const raw = await fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        block: 'construction',
        input: { file_path: filePath, extracted_text: extractedText },
        params: { action: 'auto_pipeline', doc_type: 'auto' },
      }),
    });
    return unwrapResult<ConstructionApiResult>(raw);
  },

  // Trigger a subsequent construction action with pipeline context
  async runAction(action: string, ctx: Omit<PipelineCtx, 'fileName'>): Promise<ConstructionApiResult> {
    const raw = await fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        block: 'construction',
        input: {
          file_path: ctx.file_path,
          extracted_text: ctx.extracted_text,
          quantities: ctx.quantities || {},
          line_items: ctx.costLineItems || [],
        },
        params: { action },
      }),
    });
    return unwrapResult<ConstructionApiResult>(raw);
  },

  // Drive — local needs no API call (native file picker); server uses local_drive block
  async connectDrive(type: string): Promise<{ success: boolean; files?: FileNode[] }> {
    if (type === 'local') {
      return { success: true, files: [] };
    }
    if (type === 'server') {
      const raw = await fetchApi('/v1/execute', {
        method: 'POST',
        body: JSON.stringify({
          block: 'local_drive',
          input: null,
          params: { operation: 'list', folder_path: './' },
        }),
      });
      const inner = unwrapResult<{ files?: (RawDriveFile | string)[]; items?: (RawDriveFile | string)[] }>(raw);
      const rawFiles: (RawDriveFile | string)[] = inner.files || inner.items || [];
      const fileNodes: FileNode[] = rawFiles.map((f, i) => {
        if (typeof f === 'string') {
          return { id: `server-file-${i}`, name: f, type: 'file', path: f };
        }
        const name = f.name || f.filename || '';
        const isDir = f.type === 'directory' || f.is_dir === true || f.is_folder === true;
        const path = f.path || f.file_path || f.name || '';
        return { id: `server-file-${i}`, name, type: isDir ? 'folder' : 'file', path };
      });
      return { success: true, files: fileNodes };
    }
    return fetchApi('/drive/connect', {
      method: 'POST',
      body: JSON.stringify({ type }),
    }) as Promise<{ success: boolean; files?: FileNode[] }>;
  },

  // Generic one-off block call (used for ZVec, etc.)
  async runBlock(block: string, input: unknown, params: Record<string, unknown>): Promise<unknown> {
    const raw = await fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({ block, input, params }),
    });
    return unwrapResult<unknown>(raw);
  },

  // Health check
  async health(): Promise<{ status: string }> {
    return fetchApi('/health') as Promise<{ status: string }>;
  },
};

interface RawDocumentInfoData {
  doc_type?: string;
  type?: string;
  title?: string;
  project?: string;
  pages?: number;
  total_pages?: number;
  author?: string;
  drawn_by?: string;
  date?: string;
}

interface RawQuantityValue {
  qty?: number;
  quantity?: number;
  total?: number;
  unit?: string;
}

interface RawCostEstimateData {
  subtotal?: number;
  total?: number;
  overhead?: number;
  contingency?: number;
  currency?: string;
}

interface RawContractData {
  extracted_clauses?: Record<string, { found?: boolean; examples?: string[] }>;
  clauses?: RawContractClause[];
}

// Map auto_pipeline panels array response to typed panel state
export function mapConstructionResult(result: ConstructionApiResult | null | undefined): {
  documentInfo: DocumentInfo | null;
  quantities: QuantityItem[];
  costEstimate: CostEstimate | null;
  risks: Risk[];
  submittals: Submittal[];
  schedule: ScheduleItem[];
  contract: ContractClause[];
  procurement: ProcurementItem[];
} {
  const empty = {
    documentInfo: null, quantities: [], costEstimate: null,
    risks: [], submittals: [], schedule: [], contract: [], procurement: [],
  };

  if (!result || result.status === 'error') return empty;

  const panels: RawPanel[] = result.panels || [];
  const getPanel = <T = unknown>(type: string): RawPanel<T> | undefined =>
    panels.find(p => p.type === type) as RawPanel<T> | undefined;

  const docPanel = getPanel<RawDocumentInfoData>('document_info');
  const qPanel = getPanel<Record<string, number | RawQuantityValue> | RawQuantityValue[]>('quantities');
  const costPanel = getPanel<RawCostEstimateData>('cost_estimate');
  const riskPanel = getPanel<RawRisk[]>('risks');
  const submittalPanel = getPanel<RawSubmittal[] | { submittals?: RawSubmittal[] }>('submittals');
  const schedulePanel = getPanel<RawScheduleActivity[] | { activities?: RawScheduleActivity[] }>('schedule');
  const contractPanel = getPanel<RawContractData | RawContractClause[]>('contract');
  const procurementPanel = getPanel<RawProcurementItem[] | { procurement_list?: RawProcurementItem[] }>('procurement');

  const documentInfo: DocumentInfo | null = docPanel?.data
    ? {
        type: docPanel.data.doc_type || docPanel.data.type || 'Document',
        title: docPanel.data.title || result.file_name?.replace(/\.[^/.]+$/, '') || 'Document',
        project: docPanel.data.project || 'Unknown Project',
        pages: docPanel.data.pages || docPanel.data.total_pages || 1,
        author: docPanel.data.author || docPanel.data.drawn_by || 'Unknown',
        date: docPanel.data.date || new Date().toISOString().split('T')[0],
      }
    : null;

  const quantities: QuantityItem[] = (() => {
    const q = qPanel?.data;
    if (!q) return [];
    if (Array.isArray(q)) {
      return q.map(v => ({
        item: '',
        quantity: v.qty ?? v.quantity ?? v.total ?? 0,
        unit: v.unit ?? 'units',
      }));
    }
    return Object.entries(q).map(([item, data]) => ({
      item: item.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      quantity: typeof data === 'object' ? data.qty ?? data.quantity ?? data.total ?? 0 : Number(data),
      unit: typeof data === 'object' ? data.unit ?? 'units' : 'units',
    }));
  })();

  const costEstimate: CostEstimate | null = costPanel?.data
    ? {
        subtotal: costPanel.data.subtotal ?? costPanel.data.total ?? 0,
        overhead: costPanel.data.overhead ?? 0,
        contingency: costPanel.data.contingency ?? 0,
        total: costPanel.data.total ?? costPanel.data.subtotal ?? 0,
        currency: costPanel.data.currency ?? '$',
      }
    : null;

  const risks: Risk[] = (riskPanel?.data || []).map((r, i) => ({
    id: String(r.id ?? i + 1),
    description: r.description || r.risk || r.item || 'Unknown risk',
    severity: ((r.severity || r.level || 'MEDIUM').toUpperCase()) as Risk['severity'],
    category: r.category || r.type || 'General',
    mitigation: r.mitigation || r.recommendation || '',
  }));

  return {
    documentInfo,
    quantities,
    costEstimate,
    risks,
    submittals: (() => {
      const d = submittalPanel?.data;
      const raw: RawSubmittal[] = Array.isArray(d)
        ? d
        : (Array.isArray(d?.submittals) ? d.submittals : []);
      return raw.map((s, i) => ({
        id: String(s.id ?? i + 1),
        item: s.item || s.name || s.description || 'Unknown',
        status: ((s.status || 'PENDING').toUpperCase()) as Submittal['status'],
        category: s.category || s.type || 'General',
      }));
    })(),
    schedule: (() => {
      const d = schedulePanel?.data;
      const raw: RawScheduleActivity[] = Array.isArray(d)
        ? d
        : (Array.isArray(d?.activities) ? d.activities : []);
      return raw.map((a, i) => {
        const progress = a.progress ?? a.percent_complete ?? 0;
        return {
          id: String(a.id ?? i + 1),
          task: a.task || a.name || a.activity_name || 'Unknown',
          start: a.start || a.start_date || '',
          end: a.end || a.finish || a.end_date || '',
          duration: a.duration ?? a.duration_days ?? 0,
          progress,
          status: (a.status || (progress >= 100 ? 'COMPLETED' : progress > 0 ? 'IN_PROGRESS' : 'NOT_STARTED')) as ScheduleItem['status'],
        };
      });
    })(),
    contract: (() => {
      const d = contractPanel?.data;
      if (d && !Array.isArray(d) && d.extracted_clauses && typeof d.extracted_clauses === 'object') {
        return Object.entries(d.extracted_clauses).map(([key, val], i) => ({
          id: String(i + 1),
          title: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          content: val?.examples?.[0] || '',
          section: val?.found ? 'Found' : 'Not Found',
        }));
      }
      const raw: RawContractClause[] = Array.isArray(d)
        ? d
        : (d && Array.isArray(d.clauses) ? d.clauses : []);
      return raw.map((c, i) => ({
        id: String(c.id ?? i + 1),
        title: c.title || c.name || 'Unknown',
        content: c.content || c.text || '',
        section: c.section || '',
      }));
    })(),
    procurement: (() => {
      const d = procurementPanel?.data;
      const raw: RawProcurementItem[] = Array.isArray(d)
        ? d
        : (Array.isArray(d?.procurement_list) ? d.procurement_list : []);
      return raw.map((item, i) => ({
        id: String(item.id ?? i + 1),
        item: item.item || item.name || 'Unknown',
        quantity: item.quantity ?? 0,
        unit: item.unit || 'units',
        leadTime: item.lead_time_weeks ?? item.lead_time_days ?? item.lead_time ?? 0,
        critical: item.priority === 'critical' || item.critical === true,
        supplier: item.supplier_type || item.supplier || undefined,
        status: item.status || 'PENDING',
      }));
    })(),
  };
}
