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
} from '@/types';

const API_BASE =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : 'https://cerebrum-platform-api-fork.onrender.com';

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

  // Upload — multipart, no extra fields; returns file_path (absolute server path)
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
    // UniversalBlock wraps in {block, status, result: {...}}
    const inner = result.result ?? result;
    return inner.text || inner.content || '';
  },

  // Run construction intelligence analysis
  async analyzeConstruction(filePath: string, extractedText: string): Promise<any> {
    const result = await fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        block: 'construction',
        input: {
          action: 'process_document',
          file_path: filePath,
          extracted_text: extractedText,
        },
        params: { doc_type: 'auto' },
      }),
    });
    return result.result ?? result;
  },

  // Actions — routed through the construction block
  async generateProcurementList(_fileId: string): Promise<any> {
    return fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        block: 'construction',
        input: { action: 'procurement_list_generator' },
        params: {},
      }),
    });
  },

  async trackProgress(_fileId: string): Promise<any> {
    return fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        block: 'construction',
        input: { action: 'progress_tracker' },
        params: {},
      }),
    });
  },

  async generatePaymentCertificate(_fileId: string): Promise<any> {
    return fetchApi('/v1/execute', {
      method: 'POST',
      body: JSON.stringify({
        block: 'construction',
        input: { action: 'payment_certificate' },
        params: {},
      }),
    });
  },

  // Drive — local type needs no API call
  async connectDrive(type: string, _credentials?: any): Promise<{ success: boolean; files?: any[] }> {
    if (type === 'local') {
      return { success: true, files: [] };
    }
    return fetchApi('/drive/connect', {
      method: 'POST',
      body: JSON.stringify({ type }),
    });
  },

  // Health check
  async health(): Promise<{ status: string }> {
    return fetchApi('/health');
  },
};

// Map construction block response to typed panel state
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
  if (!result || result.status === 'error') {
    return {
      documentInfo: null, quantities: [], costEstimate: null,
      risks: [], submittals: [], schedule: [], contract: [], procurement: [],
    };
  }

  const documentInfo: DocumentInfo | null = result.file_name
    ? {
        type: result.doc_type || 'Document',
        title: result.title_block?.title || result.file_name?.replace(/\.[^/.]+$/, '') || 'Document',
        project: result.title_block?.project || 'Unknown Project',
        pages: result.total_pages || 1,
        author: result.title_block?.drawn_by || 'Unknown',
        date: result.title_block?.date || new Date().toISOString().split('T')[0],
      }
    : null;

  const quantities: QuantityItem[] = (() => {
    const q = result.quantities;
    if (!q) return [];
    if (Array.isArray(q)) return q;
    // Convert dict {concrete: {qty, unit}} to array
    return Object.entries(q).map(([item, data]: [string, any]) => ({
      item: item.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      quantity: typeof data === 'object' ? data.qty ?? data.quantity ?? data.total ?? 0 : Number(data),
      unit: typeof data === 'object' ? data.unit ?? 'units' : 'units',
    }));
  })();

  const costEstimate: CostEstimate | null = result.cost_estimate
    ? {
        subtotal: result.cost_estimate.subtotal ?? result.cost_estimate.total ?? 0,
        overhead: result.cost_estimate.overhead ?? 0,
        contingency: result.cost_estimate.contingency ?? 0,
        total: result.cost_estimate.total ?? result.cost_estimate.subtotal ?? 0,
        currency: result.cost_estimate.currency ?? '$',
      }
    : null;

  const risks: Risk[] = (result.auto_risks || result.risks || []).map((r: any, i: number) => ({
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
    submittals: result.submittals || [],
    schedule: result.schedule || result.activities || [],
    contract: result.contract || result.clauses || [],
    procurement: result.procurement || result.materials || [],
  };
}
