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

const API_BASE =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : 'https://cerebrum-platform-api.onrender.com';

const API_KEY = 'cb_master_22347732f8f09bed3ad4aee7f9849f77';

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
  // Chat — sends the last user message as a string
  async sendMessage(messages: Message[]): Promise<{ text: string; response?: string }> {
    const lastUser = [...messages].reverse().find(m => m.role === 'user');
    return fetchApi('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message: lastUser?.content || '',
        model: 'deepseek-chat',
        stream: false,
      }),
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
      const fileNodes = rawFiles.map((f: any, i: number) => ({
        id: `server-file-${i}`,
        name: f.name || f.filename || String(f),
        type: (f.type === 'directory' || f.is_dir || f.is_folder) ? 'folder' : 'file',
        path: f.path || f.file_path || f.name || '',
      }));
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
    submittals: Array.isArray(submittalPanel?.data) ? submittalPanel.data : [],
    schedule: Array.isArray(schedulePanel?.data) ? schedulePanel.data : [],
    contract: Array.isArray(contractPanel?.data) ? contractPanel.data : [],
    procurement: Array.isArray(procurementPanel?.data) ? procurementPanel.data : [],
  };
}
