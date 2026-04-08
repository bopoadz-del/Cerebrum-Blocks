/**
 * Cerebrum API Client
 */

import { ChatResponse, StreamChunk } from './response';
import {
  CerebrumError,
  AuthenticationError,
  RateLimitError,
  BlockNotFoundError,
  ExecutionError,
} from './errors';
import {
  ChatOptions,
  StreamOptions,
  BlockParams,
  ChainStep,
  UsageStats,
  BlockInfo,
  VectorDocument,
  VectorResult,
} from './types';

/** Client configuration options */
export interface CerebrumConfig {
  /** Your Cerebrum API key (starts with 'cb_') */
  apiKey: string;
  /** API endpoint URL (default: https://api.cerebrumblocks.com) */
  baseUrl?: string;
  /** Request timeout in milliseconds (default: 60000) */
  timeout?: number;
}

/**
 * Official Cerebrum API Client
 * 
 * Build AI applications with modular blocks. One API key, 16 blocks,
 * infinite possibilities.
 * 
 * @example
 * ```javascript
 * import { Cerebrum } from 'cerebrum-js';
 * 
 * // Initialize with API key
 * const client = new Cerebrum({ apiKey: 'cb_your_key_here' });
 * 
 * // Simple chat
 * const response = await client.chat('Explain quantum computing');
 * console.log(response.text);
 * 
 * // Streaming chat
 * for await (const chunk of client.chat.stream('Tell me a story')) {
 *   process.stdout.write(chunk.text);
 * }
 * ```
 */
export class Cerebrum {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;
  
  static readonly DEFAULT_BASE_URL = 'https://api.cerebrumblocks.com';
  
  constructor(config: CerebrumConfig) {
    if (!config.apiKey) {
      throw new AuthenticationError(
        'API key required. Get one at https://cerebrumblocks.com/dashboard\n' +
        'Set CEREBRUM_API_KEY environment variable or pass apiKey to constructor'
      );
    }
    
    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl || Cerebrum.DEFAULT_BASE_URL).replace(/\/$/, '');
    this.timeout = config.timeout || 60000;
  }
  
  /** Get request headers */
  private headers(): Record<string, string> {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
      'User-Agent': 'cerebrum-js/1.0.0',
    };
  }
  
  /** Make HTTP request and handle errors */
  private async request(
    method: string,
    endpoint: string,
    body?: Record<string, any>
  ): Promise<Record<string, any>> {
    const url = `${this.baseUrl}/v1${endpoint}`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    
    try {
      const response = await fetch(url, {
        method,
        headers: this.headers(),
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.status === 401) {
        throw new AuthenticationError();
      } else if (response.status === 429) {
        throw new RateLimitError();
      } else if (response.status === 404) {
        throw new BlockNotFoundError(`Endpoint not found: ${endpoint}`);
      } else if (response.status >= 500) {
        const text = await response.text();
        throw new ExecutionError(`Server error: ${text}`);
      }
      
      if (!response.ok) {
        const text = await response.text();
        throw new CerebrumError(`HTTP ${response.status}: ${text}`, response.status);
      }
      
      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof CerebrumError) {
        throw error;
      }
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new CerebrumError('Request timeout');
        }
        throw new CerebrumError(`Request failed: ${error.message}`);
      }
      
      throw new CerebrumError('Unknown error');
    }
  }
  
  // -------------------- CHAT --------------------
  
  /**
   * Send a chat message
   * @param message - The message to send
   * @param options - Additional options
   * @returns ChatResponse with .text, .tokensUsed, .model
   * 
   * @example
   * const response = await client.chat('Hello!');
   * console.log(response.text);
   */
  async chat(message: string, options: ChatOptions = {}): Promise<ChatResponse> {
    const result = await this.request('POST', '/chat', {
      message,
      model: options.model || 'gpt-3.5-turbo',
      system: options.system || 'You are a helpful assistant.',
      max_tokens: options.maxTokens || 1000,
      temperature: options.temperature ?? 0.7,
      provider: options.provider || 'openai',
    });
    
    return new ChatResponse(result);
  }
  
  /**
   * Stream a chat response token by token
   * @param message - The message to send
   * @param options - Additional options
   * @returns AsyncGenerator of StreamChunk
   * 
   * @example
   * for await (const chunk of client.chatStream('Tell me a story')) {
   *   process.stdout.write(chunk.text);
   * }
   */
  async *chatStream(message: string, options: StreamOptions = {}): AsyncGenerator<StreamChunk> {
    const url = `${this.baseUrl}/v1/chat/stream`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({
        message,
        model: options.model || 'gpt-3.5-turbo',
        system: options.system || 'You are a helpful assistant.',
        max_tokens: options.maxTokens || 1000,
        temperature: options.temperature ?? 0.7,
        provider: options.provider || 'openai',
      }),
    });
    
    if (response.status === 401) {
      throw new AuthenticationError();
    } else if (response.status === 429) {
      throw new RateLimitError();
    }
    
    if (!response.ok) {
      throw new CerebrumError(`HTTP ${response.status}`);
    }
    
    const reader = response.body?.getReader();
    if (!reader) {
      throw new CerebrumError('No response body');
    }
    
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          
          try {
            const chunk = JSON.parse(data);
            yield new StreamChunk(chunk);
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  }
  
  /** Access streaming methods via client.chat.stream() */
  get chatStreamAccessor() {
    const self = this;
    return {
      stream: (message: string, options?: StreamOptions) => self.chatStream(message, options),
    };
  }
  
  // -------------------- BLOCKS --------------------
  
  /**
   * List all available blocks for your tier
   * @returns Array of block definitions
   * 
   * @example
   * const blocks = await client.listBlocks();
   * for (const block of blocks) {
   *   console.log(`${block.name}: ${block.description}`);
   * }
   */
  async listBlocks(): Promise<BlockInfo[]> {
    const result = await this.request('GET', '/blocks');
    return result.blocks || [];
  }
  
  /**
   * Execute a single block
   * @param block - Block name (chat, pdf, ocr, etc.)
   * @param input - Input for the block
   * @param params - Optional parameters
   * @returns Block execution result
   * 
   * @example
   * const result = await client.execute('pdf', 'document.pdf', { extract: 'text' });
   * console.log(result.text);
   */
  async execute(block: string, input: any, params?: BlockParams): Promise<Record<string, any>> {
    return this.request('POST', '/execute', {
      block,
      input,
      params: params || {},
    });
  }
  
  /**
   * Execute a chain of blocks
   * @param steps - Array of {block, params}
   * @param initialInput - Starting input for the chain
   * @returns Chain execution result
   * 
   * @example
   * const result = await client.chain([
   *   { block: 'pdf', params: { extract: 'text' } },
   *   { block: 'chat', params: { prompt: 'Summarize:' } }
   * ], 'document.pdf');
   */
  async chain(steps: ChainStep[], initialInput: any): Promise<Record<string, any>> {
    return this.request('POST', '/chain', {
      steps,
      initial_input: initialInput,
    });
  }
  
  // -------------------- VECTOR SEARCH --------------------
  
  /**
   * Add documents to vector search
   * @param documents - Array of {text, metadata} objects
   * @param collection - Collection name
   * 
   * @example
   * await client.vectorAdd([
   *   { text: 'Hello world', metadata: { source: 'example' } }
   * ], 'docs');
   */
  async vectorAdd(documents: VectorDocument[], collection: string = 'default'): Promise<Record<string, any>> {
    return this.request('POST', '/vector/add', {
      documents,
      collection,
    });
  }
  
  /**
   * Search vector database
   * @param query - Search query
   * @param collection - Collection name
   * @param topK - Number of results
   * @returns Array of matching documents with scores
   * 
   * @example
   * const results = await client.vectorSearch('AI technology', undefined, 3);
   * for (const doc of results) {
   *   console.log(`${doc.score}: ${doc.text}`);
   * }
   */
  async vectorSearch(query: string, collection: string = 'default', topK: number = 5): Promise<VectorResult[]> {
    const result = await this.request('POST', '/vector/search', {
      query,
      collection,
      top_k: topK,
    });
    return result.results || [];
  }
  
  // -------------------- USAGE --------------------
  
  /**
   * Get usage statistics for your API key
   * @param days - Number of days to look back (default: 30)
   * @returns Usage statistics
   * 
   * @example
   * const stats = await client.usage();
   * console.log(`Used ${stats.totalRequests} of ${stats.limits.requests}`);
   */
  async usage(days: number = 30): Promise<UsageStats> {
    // Extract key ID from the API key (cb_<id>_<secret>)
    const keyId = this.apiKey.split('_')[1] || 'unknown';
    const result = await this.request('GET', `/keys/${keyId}/usage?days=${days}`);
    return {
      totalRequests: result.total_requests,
      totalTokens: result.total_tokens,
      avgResponseTimeMs: result.avg_response_time_ms,
      dailyBreakdown: result.daily_breakdown,
      limits: result.limits,
    };
  }
  
  /**
   * Check API health status
   * @returns Health status, version, blocks available
   */
  async health(): Promise<Record<string, any>> {
    return this.request('GET', '/health');
  }
}

/** Alias for backward compatibility */
export const CerebrumClient = Cerebrum;
