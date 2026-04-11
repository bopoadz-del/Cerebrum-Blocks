// All 54+ blocks from the Cerebrum Block Store

export interface Block {
  name: string;
  displayName: string;
  description: string;
  price: number;
  category: string;
  tags: string[];
  icon: string;
  author: string;
  rating: number;
  reviews: number;
}

export const BLOCKS: Block[] = [
  // Domain Containers (Layer 3)
  { name: 'container_construction', displayName: 'Construction', description: 'BIM processing, PDF extraction, QA inspection for AEC', price: 299, category: 'Domain Containers', tags: ['aec', 'bim', 'construction'], icon: '🏗️', author: 'Cerebrum', rating: 4.8, reviews: 42 },
  { name: 'container_ai_core', displayName: 'AI Core', description: 'Adaptive routing, provider failover, performance leaderboard', price: 199, category: 'Domain Containers', tags: ['ai', 'routing', 'failover'], icon: '🧠', author: 'Cerebrum', rating: 4.7, reviews: 38 },
  { name: 'container_security', displayName: 'Security', description: 'Auth, secrets, sandbox, audit, rate limiting', price: 149, category: 'Domain Containers', tags: ['security', 'auth', 'sandbox'], icon: '🔐', author: 'Cerebrum', rating: 4.9, reviews: 52 },
  { name: 'container_store', displayName: 'Store', description: 'Block discovery, reviews, payment split, validation', price: 99, category: 'Domain Containers', tags: ['marketplace', 'payments'], icon: '🏪', author: 'Cerebrum', rating: 4.6, reviews: 28 },
  { name: 'container_platform', displayName: 'Platform', description: 'User management, billing, subscriptions', price: 129, category: 'Domain Containers', tags: ['platform', 'billing'], icon: '🚀', author: 'Cerebrum', rating: 4.5, reviews: 31 },
  { name: 'container_team', displayName: 'Team', description: 'Collaboration, permissions, workspaces', price: 79, category: 'Domain Containers', tags: ['team', 'collaboration'], icon: '👥', author: 'Cerebrum', rating: 4.4, reviews: 24 },
  { name: 'container_infrastructure', displayName: 'Infrastructure', description: 'HAL, config, memory, database, event bus', price: 89, category: 'Domain Containers', tags: ['infrastructure', 'hal'], icon: '🔧', author: 'Cerebrum', rating: 4.7, reviews: 19 },
  { name: 'container_utility', displayName: 'Utility', description: 'Helper blocks, format converters, validators', price: 49, category: 'Domain Containers', tags: ['utility', 'helpers'], icon: '🛠️', author: 'Cerebrum', rating: 4.3, reviews: 15 },
  
  // AI Core (Layer 2)
  { name: 'chat', displayName: 'Chat AI', description: 'Multi-provider LLM (DeepSeek, Groq, OpenAI)', price: 49, category: 'AI Core', tags: ['ai', 'llm', 'chat'], icon: '💬', author: 'Cerebrum', rating: 4.9, reviews: 156 },
  { name: 'vector', displayName: 'Vector Search', description: 'Semantic search with ChromaDB embeddings', price: 49, category: 'AI Core', tags: ['ai', 'vector', 'search'], icon: '🔍', author: 'Cerebrum', rating: 4.7, reviews: 89 },
  { name: 'image', displayName: 'Image AI', description: 'Image analysis and generation', price: 39, category: 'AI Core', tags: ['ai', 'vision', 'image'], icon: '🖼️', author: 'Cerebrum', rating: 4.5, reviews: 67 },
  { name: 'voice', displayName: 'Voice AI', description: 'Text-to-speech and speech-to-text', price: 39, category: 'AI Core', tags: ['ai', 'audio', 'tts'], icon: '🔊', author: 'Cerebrum', rating: 4.4, reviews: 45 },
  { name: 'translate', displayName: 'Translate', description: '100+ language translation', price: 29, category: 'AI Core', tags: ['ai', 'nlp', 'translation'], icon: '🌐', author: 'Cerebrum', rating: 4.6, reviews: 78 },
  { name: 'code', displayName: 'Code AI', description: 'Code generation and execution', price: 29, category: 'AI Core', tags: ['ai', 'code', 'developer'], icon: '💻', author: 'Cerebrum', rating: 4.5, reviews: 91 },
  { name: 'search', displayName: 'Search', description: 'Web search with multiple providers', price: 19, category: 'AI Core', tags: ['ai', 'search', 'web'], icon: '🔎', author: 'Cerebrum', rating: 4.3, reviews: 56 },
  { name: 'web', displayName: 'Web Scraper', description: 'Extract data from websites', price: 25, category: 'AI Core', tags: ['ai', 'web', 'scraping'], icon: '🕸️', author: 'Cerebrum', rating: 4.4, reviews: 43 },
  
  // Documents (Layer 3)
  { name: 'pdf', displayName: 'PDF Processor', description: 'Extract text, tables, images from PDFs', price: 29, category: 'Documents', tags: ['pdf', 'documents', 'extraction'], icon: '📄', author: 'Cerebrum', rating: 4.6, reviews: 112 },
  { name: 'ocr', displayName: 'OCR', description: 'Text extraction from images and PDFs', price: 29, category: 'Documents', tags: ['ocr', 'vision', 'documents'], icon: '👁️', author: 'Cerebrum', rating: 4.5, reviews: 89 },
  { name: 'documentation', displayName: 'Documentation', description: 'Auto-generate docs from code', price: 35, category: 'Documents', tags: ['docs', 'documentation'], icon: '📚', author: 'Cerebrum', rating: 4.2, reviews: 34 },
  
  // Security (Layer 1)
  { name: 'auth', displayName: 'Auth', description: 'API key management, RBAC, multi-tenancy', price: 59, category: 'Security', tags: ['security', 'auth', 'rbac'], icon: '🔑', author: 'Cerebrum', rating: 4.8, reviews: 67 },
  { name: 'secrets', displayName: 'Secrets', description: 'Secure credential storage and rotation', price: 49, category: 'Security', tags: ['security', 'secrets'], icon: '🗝️', author: 'Cerebrum', rating: 4.7, reviews: 42 },
  { name: 'rate_limiter', displayName: 'Rate Limiter', description: 'Sliding window rate limiting', price: 39, category: 'Security', tags: ['security', 'rate-limiting'], icon: '⏱️', author: 'Cerebrum', rating: 4.5, reviews: 38 },
  { name: 'sandbox', displayName: 'Sandbox', description: 'Code execution sandbox', price: 45, category: 'Security', tags: ['security', 'sandbox'], icon: '🏖️', author: 'Cerebrum', rating: 4.6, reviews: 29 },
  { name: 'audit', displayName: 'Audit', description: 'Event logging and compliance tracking', price: 55, category: 'Security', tags: ['security', 'audit', 'compliance'], icon: '📋', author: 'Cerebrum', rating: 4.4, reviews: 31 },
  { name: 'validation', displayName: 'Validation', description: 'Input validation and sanitization', price: 25, category: 'Security', tags: ['security', 'validation'], icon: '✅', author: 'Cerebrum', rating: 4.3, reviews: 27 },
  
  // Infrastructure (Layer 0)
  { name: 'hal', displayName: 'HAL', description: 'Hardware abstraction layer', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'hal'], icon: '🔌', author: 'Cerebrum', rating: 4.8, reviews: 22 },
  { name: 'config', displayName: 'Config', description: 'Configuration management', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'config'], icon: '⚙️', author: 'Cerebrum', rating: 4.5, reviews: 18 },
  { name: 'memory', displayName: 'Memory', description: 'High-speed cache with TTL and LRU', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'cache'], icon: '🧠', author: 'Cerebrum', rating: 4.6, reviews: 34 },
  { name: 'database', displayName: 'Database', description: 'Database connector and ORM', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'database'], icon: '🗄️', author: 'Cerebrum', rating: 4.4, reviews: 41 },
  { name: 'storage', displayName: 'Storage', description: 'File storage and retrieval', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'storage'], icon: '💾', author: 'Cerebrum', rating: 4.3, reviews: 29 },
  { name: 'queue', displayName: 'Queue', description: 'Background job queue', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'queue'], icon: '📬', author: 'Cerebrum', rating: 4.5, reviews: 36 },
  { name: 'event_bus', displayName: 'Event Bus', description: 'Cross-block messaging system', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'events'], icon: '🔔', author: 'Cerebrum', rating: 4.7, reviews: 25 },
  { name: 'migration', displayName: 'Migration', description: 'Database migration tools', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'migration'], icon: '🚚', author: 'Cerebrum', rating: 4.2, reviews: 19 },
  { name: 'failover', displayName: 'Failover', description: 'Circuit breaker and failover', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'reliability'], icon: '🔄', author: 'Cerebrum', rating: 4.6, reviews: 28 },
  
  // Monitoring (Layer 2)
  { name: 'monitoring', displayName: 'Monitoring', description: 'Metrics, logs, and alerts', price: 59, category: 'Monitoring', tags: ['monitoring', 'metrics'], icon: '📊', author: 'Cerebrum', rating: 4.7, reviews: 45 },
  { name: 'health_check', displayName: 'Health Check', description: 'Service health monitoring', price: 0, category: 'Monitoring', tags: ['monitoring', 'health'], icon: '❤️', author: 'Cerebrum', rating: 4.5, reviews: 32 },
  { name: 'error_tracking', displayName: 'Error Tracking', description: 'Error collection and analysis', price: 49, category: 'Monitoring', tags: ['monitoring', 'errors'], icon: '🐛', author: 'Cerebrum', rating: 4.4, reviews: 38 },
  { name: 'analytics', displayName: 'Analytics', description: 'Usage analytics and reporting', price: 69, category: 'Monitoring', tags: ['monitoring', 'analytics'], icon: '📈', author: 'Cerebrum', rating: 4.3, reviews: 41 },
  
  // Integration (Layer 4)
  { name: 'email', displayName: 'Email', description: 'Email sending and templates', price: 19, category: 'Integration', tags: ['integration', 'email'], icon: '📧', author: 'Cerebrum', rating: 4.4, reviews: 52 },
  { name: 'webhook', displayName: 'Webhook', description: 'Webhook handling and delivery', price: 15, category: 'Integration', tags: ['integration', 'webhooks'], icon: '🔗', author: 'Cerebrum', rating: 4.5, reviews: 47 },
  { name: 'notification', displayName: 'Notification', description: 'Multi-channel notifications', price: 25, category: 'Integration', tags: ['integration', 'notifications'], icon: '📢', author: 'Cerebrum', rating: 4.3, reviews: 39 },
  { name: 'workflow', displayName: 'Workflow', description: 'Visual workflow builder', price: 79, category: 'Integration', tags: ['integration', 'workflow'], icon: '📋', author: 'Cerebrum', rating: 4.6, reviews: 33 },
  
  // Store/Marketplace (Layer 4)
  { name: 'discovery', displayName: 'Discovery', description: 'Block recommendations and search', price: 0, category: 'Marketplace', tags: ['marketplace', 'discovery'], icon: '🔮', author: 'Cerebrum', rating: 4.5, reviews: 22 },
  { name: 'review', displayName: 'Review', description: 'Ratings and reviews system', price: 0, category: 'Marketplace', tags: ['marketplace', 'reviews'], icon: '⭐', author: 'Cerebrum', rating: 4.4, reviews: 28 },
  { name: 'payment_split', displayName: 'Payment Split', description: 'Revenue sharing and payouts', price: 0, category: 'Marketplace', tags: ['marketplace', 'payments'], icon: '💳', author: 'Cerebrum', rating: 4.7, reviews: 15 },
  { name: 'version', displayName: 'Version', description: 'Semantic versioning for blocks', price: 0, category: 'Marketplace', tags: ['marketplace', 'versioning'], icon: '🏷️', author: 'Cerebrum', rating: 4.3, reviews: 19 },
  { name: 'billing', displayName: 'Billing', description: 'Subscription and billing management', price: 0, category: 'Marketplace', tags: ['marketplace', 'billing'], icon: '💰', author: 'Cerebrum', rating: 4.6, reviews: 24 },
  { name: 'dashboard', displayName: 'Dashboard', description: 'Analytics dashboard builder', price: 59, category: 'Marketplace', tags: ['marketplace', 'dashboard'], icon: '📊', author: 'Cerebrum', rating: 4.5, reviews: 31 },
  
  // Team/Collaboration
  { name: 'team', displayName: 'Team', description: 'Team management and permissions', price: 39, category: 'Team', tags: ['team', 'collaboration'], icon: '👥', author: 'Cerebrum', rating: 4.4, reviews: 36 },
  
  // Adaptive/Router
  { name: 'adaptive_router', displayName: 'Adaptive Router', description: 'Smart routing based on latency/cost', price: 0, category: 'AI Core', tags: ['ai', 'routing', 'adaptive'], icon: '🔀', author: 'Cerebrum', rating: 4.7, reviews: 18 },
  
  // Missing blocks
  { name: 'bim', displayName: 'BIM', description: 'Building Information Modeling processing', price: 149, category: 'Domain Containers', tags: ['aec', 'bim', 'modeling'], icon: '🏢', author: 'Cerebrum', rating: 4.6, reviews: 21 },
  { name: 'container', displayName: 'Container', description: 'Hyper-Block pattern for nesting blocks', price: 0, category: 'Infrastructure', tags: ['infrastructure', 'container', 'sandbox'], icon: '📦', author: 'Cerebrum', rating: 4.5, reviews: 17 },
  
  // Drive/Storage blocks
  { name: 'google_drive', displayName: 'Google Drive', description: 'Google Drive integration and file access', price: 19, category: 'Integration', tags: ['storage', 'drive', 'google'], icon: '📁', author: 'Cerebrum', rating: 4.4, reviews: 47 },
  { name: 'onedrive', displayName: 'OneDrive', description: 'Microsoft OneDrive integration', price: 19, category: 'Integration', tags: ['storage', 'drive', 'microsoft'], icon: '☁️', author: 'Cerebrum', rating: 4.3, reviews: 38 },
  { name: 'local_drive', displayName: 'Local Drive', description: 'Local filesystem access', price: 0, category: 'Infrastructure', tags: ['storage', 'local', 'filesystem'], icon: '💿', author: 'Cerebrum', rating: 4.2, reviews: 29 },
  { name: 'android_drive', displayName: 'Android Drive', description: 'Android storage access', price: 0, category: 'Integration', tags: ['storage', 'android', 'mobile'], icon: '📱', author: 'Cerebrum', rating: 4.1, reviews: 18 },
  { name: 'vector_search', displayName: 'Vector Search', description: 'ChromaDB semantic search (alias)', price: 49, category: 'AI Core', tags: ['ai', 'vector', 'search'], icon: '🔍', author: 'Cerebrum', rating: 4.7, reviews: 89 },
  { name: 'zvec', displayName: 'ZVec', description: 'Zero-vector optimization for embeddings', price: 0, category: 'AI Core', tags: ['ai', 'vector', 'optimization'], icon: '⚡', author: 'Cerebrum', rating: 4.5, reviews: 12 },
];

export const CATEGORIES = [
  'All',
  'Domain Containers',
  'AI Core',
  'Documents',
  'Security',
  'Infrastructure',
  'Monitoring',
  'Integration',
  'Marketplace',
  'Team'
];
