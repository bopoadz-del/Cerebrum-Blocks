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

const API_BASE = 'https://cerebrum-platform-api.onrender.com';

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
  // Chat
  async sendMessage(messages: Message[], file?: File): Promise<{ response: string; panels?: any }> {
    const formData = new FormData();
    formData.append('messages', JSON.stringify(messages));
    if (file) {
      formData.append('file', file);
    }

    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new ApiError(response.status, error);
    }

    return response.json();
  },

  async uploadFile(file: File, type: 'text' | 'pdf' | 'image' | 'binary'): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new ApiError(response.status, error);
    }

    return response.json();
  },

  // Construction Intelligence
  async runAutoPipeline(fileId: string): Promise<any> {
    return fetchApi('/construction/auto_pipeline', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId }),
    });
  },

  async getDocumentInfo(fileId: string): Promise<DocumentInfo> {
    return fetchApi(`/construction/document_info?file_id=${fileId}`);
  },

  async getQuantities(fileId: string): Promise<QuantityItem[]> {
    return fetchApi(`/construction/quantities?file_id=${fileId}`);
  },

  async getCostEstimate(fileId: string): Promise<CostEstimate> {
    return fetchApi(`/construction/cost_estimate?file_id=${fileId}`);
  },

  async getRisks(fileId: string): Promise<Risk[]> {
    return fetchApi(`/construction/risks?file_id=${fileId}`);
  },

  async getSubmittals(fileId: string): Promise<Submittal[]> {
    return fetchApi(`/construction/submittals?file_id=${fileId}`);
  },

  async getSchedule(fileId: string): Promise<ScheduleItem[]> {
    return fetchApi(`/construction/schedule?file_id=${fileId}`);
  },

  async getContract(fileId: string): Promise<ContractClause[]> {
    return fetchApi(`/construction/contract?file_id=${fileId}`);
  },

  async getProcurement(fileId: string): Promise<ProcurementItem[]> {
    return fetchApi(`/construction/procurement?file_id=${fileId}`);
  },

  // Actions
  async generateProcurementList(fileId: string): Promise<any> {
    return fetchApi('/actions/procurement_list', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId }),
    });
  },

  async trackProgress(fileId: string): Promise<any> {
    return fetchApi('/actions/progress_tracker', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId }),
    });
  },

  async generatePaymentCertificate(fileId: string): Promise<any> {
    return fetchApi('/actions/payment_certificate', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId }),
    });
  },

  // Drive
  async connectDrive(type: string, credentials?: any): Promise<{ success: boolean; files?: any[] }> {
    return fetchApi('/drive/connect', {
      method: 'POST',
      body: JSON.stringify({ type, credentials }),
    });
  },

  async getDriveFiles(driveId: string, path?: string): Promise<any[]> {
    return fetchApi(`/drive/files?drive_id=${driveId}&path=${path || ''}`);
  },

  // Health check
  async health(): Promise<{ status: string }> {
    return fetchApi('/health');
  },
};
