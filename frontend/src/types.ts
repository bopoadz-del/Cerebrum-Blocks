export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'error';
  content: string;
  timestamp: number;
  attachments?: FileAttachment[];
}

export interface FileAttachment {
  name: string;
  type: string;
  size: number;
  content?: string;
  url?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  active?: boolean;
}

export interface DriveSource {
  id: string;
  name: string;
  icon: string;
  connected: boolean;
  type: 'local' | 'server' | 'google' | 'onedrive' | 'android' | 'dropbox';
  files?: FileNode[];
}

export interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  expanded?: boolean;
  selected?: boolean;
  path?: string;
}

export interface ConstructionPanel {
  id: string;
  title: string;
  visible: boolean;
  data?: any;
}

export interface DocumentInfo {
  type: string;
  title: string;
  project: string;
  pages: number;
  author?: string;
  date?: string;
}

export interface QuantityItem {
  item: string;
  quantity: number;
  unit: string;
}

export interface CostEstimate {
  subtotal: number;
  overhead: number;
  contingency: number;
  total: number;
  currency: string;
}

export interface Risk {
  id: string;
  description: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  category: string;
  mitigation?: string;
}

export interface Submittal {
  id: string;
  item: string;
  status: 'APPROVED' | 'PENDING' | 'REJECTED' | 'REQUIRED';
  category: string;
}

export interface ScheduleItem {
  id: string;
  task: string;
  start: string;
  end: string;
  duration: number;
  progress: number;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'DELAYED';
}

export interface ContractClause {
  id: string;
  title: string;
  content: string;
  section: string;
}

export interface ProcurementItem {
  id: string;
  item: string;
  quantity: number;
  unit: string;
  leadTime: number;
  critical: boolean;
  supplier?: string;
  status: string;
}

export interface ProcessingState {
  active: boolean;
  stage: string;
  progress: number;
}

export type Theme = 'light' | 'dark';

export type PanelType = 
  | 'documentInfo'
  | 'quantities'
  | 'costEstimate'
  | 'risks'
  | 'submittals'
  | 'schedule'
  | 'contract'
  | 'procurement';
