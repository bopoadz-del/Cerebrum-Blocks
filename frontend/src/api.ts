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

async function fetchApi(path: string, options?: RequestInit): Promise<any> {
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
    });
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
    const result = await fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        block,
        input: { file_path: filePath },
        params: {},
      }),
    });
    const inner = result.result ?? result;
    return inner.text || inner.content || '';
  },

  // Run construction auto_pipeline — action must be in params, NOT in input
  async analyzeConstruction(filePath: string, extractedText: string): Promise<any> {
    const result = await fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        block: 'construction',
        input: { file_path: filePath, extracted_text: extractedText },
        params: { action: 'auto_pipeline', doc_type: 'auto' },
      }),
    });
    return result.result ?? result;
  },

  // Trigger a subsequent construction action with pipeline context
  async runAction(action: string, ctx: Omit<PipelineCtx, 'fileName'>): Promise<any> {
    const result = await fetchApi('/v1/execute', {
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
    return result.result ?? result;
  },

  // Drive — local needs no API call (native file picker); server uses local_drive block
  async connectDrive(type: string): Promise<{ success: boolean; files?: any[] }> {
    if (type === 'local') {
      return { success: true, files: [] };
    }
    if (type === 'server') {
      const result = await fetchApi('/v1/execute', {
        method: 'POST',
        body: JSON.stringify({
          block: 'local_drive',
          input: null,
          params: { operation: 'list', folder_path: './' },
        }),
      });
      const inner = result.result ?? result;
      const rawFiles: any[] = inner.files || inner.items || [];
      const fileNodes = rawFiles.map((f: any, i: number) => {
        const name = typeof f === 'string' ? f : (f.name || f.filename || String(f));
        const isDir = typeof f === 'object' && (f.type === 'directory' || f.is_dir || f.is_folder);
        const path = typeof f === 'string' ? f : (f.path || f.file_path || f.name || f);
        return { id: `server-file-${i}`, name, type: isDir ? 'folder' : 'file', path };
      });
      return { success: true, files: fileNodes };
    }
    return fetchApi('/drive/connect', {
      method: 'POST',
      body: JSON.stringify({ type }),
    });
  },

  // Generic one-off block call (used for ZVec, etc.)
  async runBlock(block: string, input: any, params: any): Promise<any> {
    const result = await fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({ block, input, params }),
    });
    return result.result ?? result;
  },

  // Health check
  async health(): Promise<{ status: string }> {
    return fetchApi('/health');
  },
};

// Map auto_pipeline panels array response to typed panel state
export function mapConstructionResult(result: any): {
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

  const panels: any[] = result.panels || [];
  const getPanel = (type: string) => panels.find((p: any) => p.type === type);

  const docPanel = getPanel('document_info');
  const qPanel = getPanel('quantities');
  const costPanel = getPanel('cost_estimate');
  const riskPanel = getPanel('risks');
  const submittalPanel = getPanel('submittals');
  const schedulePanel = getPanel('schedule');
  const contractPanel = getPanel('contract');
  const procurementPanel = getPanel('procurement');

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
    if (Array.isArray(q)) return q;
    return Object.entries(q).map(([item, data]: [string, any]) => ({
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

  const risks: Risk[] = (riskPanel?.data || []).map((r: any, i: number) => ({
    id: r.id ?? String(i + 1),
    description: r.description || r.risk || r.item || 'Unknown risk',
    severity: (r.severity || r.level || 'MEDIUM').toUpperCase() as Risk['severity'],
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
      const raw: any[] = Array.isArray(d) ? d : (Array.isArray(d?.submittals) ? d.submittals : []);
      return raw.map((s: any, i: number) => ({
        id: s.id ?? String(i + 1),
        item: s.item || s.name || s.description || 'Unknown',
        status: (s.status || 'PENDING').toUpperCase() as Submittal['status'],
        category: s.category || s.type || 'General',
      }));
    })(),
    schedule: (() => {
      const d = schedulePanel?.data;
      const raw: any[] = Array.isArray(d) ? d : (Array.isArray(d?.activities) ? d.activities : []);
      return raw.map((a: any, i: number) => ({
        id: a.id ?? String(i + 1),
        task: a.task || a.name || a.activity_name || 'Unknown',
        start: a.start || a.start_date || '',
        end: a.end || a.finish || a.end_date || '',
        duration: a.duration ?? a.duration_days ?? 0,
        progress: a.progress ?? a.percent_complete ?? 0,
        status: (a.status || (a.progress >= 100 ? 'COMPLETED' : a.progress > 0 ? 'IN_PROGRESS' : 'NOT_STARTED')) as ScheduleItem['status'],
      }));
    })(),
    contract: (() => {
      const d = contractPanel?.data;
      const clauses = d?.extracted_clauses;
      if (clauses && typeof clauses === 'object' && !Array.isArray(clauses)) {
        return Object.entries(clauses).map(([key, val]: [string, any], i) => ({
          id: String(i + 1),
          title: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          content: (val?.examples?.[0] || '') as string,
          section: val?.found ? 'Found' : 'Not Found',
        }));
      }
      const raw: any[] = Array.isArray(d) ? d : (Array.isArray(d?.clauses) ? d.clauses : []);
      return raw.map((c: any, i: number) => ({
        id: c.id ?? String(i + 1),
        title: c.title || c.name || 'Unknown',
        content: c.content || c.text || '',
        section: c.section || '',
      }));
    })(),
    procurement: (() => {
      const d = procurementPanel?.data;
      const raw: any[] = Array.isArray(d) ? d : (Array.isArray(d?.procurement_list) ? d.procurement_list : []);
      return raw.map((item: any, i: number) => ({
        id: item.id ?? String(i + 1),
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
