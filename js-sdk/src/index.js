/**
 * Cerebrum Blocks JavaScript SDK
 * 
 * Build AI like Lego. One API. 13 blocks.
 * 
 * @example
 * import { CerebrumClient } from 'cerebrum-blocks';
 * 
 * const client = new CerebrumClient({ apiKey: 'your-key' });
 * const response = await client.chat('Hello!');
 * console.log(response.text);
 */

export class CerebrumClient {
  /**
   * Create a Cerebrum client.
   * @param {Object} options
   * @param {string} options.apiKey - Your Cerebrum API key
   * @param {string} [options.baseUrl='https://api.cerebrumblocks.com'] - API endpoint
   */
  constructor({ apiKey, baseUrl = 'https://api.cerebrumblocks.com' } = {}) {
    this.apiKey = apiKey || process.env.CEREBRUM_API_KEY;
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  _headers() {
    const headers = {
      'Content-Type': 'application/json',
    };
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }
    return headers;
  }

  async _post(endpoint, body) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: this._headers(),
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cerebrum API error: ${response.status} ${error}`);
    }

    return response.json();
  }

  async _get(endpoint) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'GET',
      headers: this._headers(),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cerebrum API error: ${response.status} ${error}`);
    }

    return response.json();
  }

  // -------------------- CHAT --------------------

  /**
   * Send a chat message.
   * @param {string} message - The message to send
   * @param {Object} [options={}] - Additional options
   * @param {string} [options.model='gpt-3.5-turbo'] - Model to use
   * @param {string} [options.system='You are a helpful assistant.'] - System prompt
   * @param {number} [options.maxTokens=1000] - Maximum tokens
   * @param {number} [options.temperature=0.7] - Sampling temperature
   * @param {string} [options.provider='openai'] - Provider: 'openai', 'anthropic', 'mock'
   * @returns {Promise<ChatResponse>}
   */
  async chat(message, options = {}) {
    const result = await this._post('/v1/chat', {
      message,
      model: options.model || 'gpt-3.5-turbo',
      system: options.system || 'You are a helpful assistant.',
      max_tokens: options.maxTokens || options.max_tokens || 1000,
      temperature: options.temperature || 0.7,
      provider: options.provider || 'openai',
    });
    return new ChatResponse(result);
  }

  /**
   * Stream a chat response.
   * @param {string} message - The message to send
   * @param {Object} [options={}] - Additional options
   * @returns {AsyncGenerator<StreamChunk>}
   * @example
   * const stream = await client.chat.stream('Tell me a story');
   * for await (const chunk of stream) {
   *   process.stdout.write(chunk.text);
   * }
   */
  async *chatStream(message, options = {}) {
    const response = await fetch(`${this.baseUrl}/v1/chat/stream`, {
      method: 'POST',
      headers: this._headers(),
      body: JSON.stringify({
        message,
        model: options.model || 'gpt-3.5-turbo',
        system: options.system || 'You are a helpful assistant.',
        max_tokens: options.maxTokens || options.max_tokens || 1000,
        temperature: options.temperature || 0.7,
        provider: options.provider || 'openai',
        stream: true,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Cerebrum API error: ${response.status} ${error}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

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

  // -------------------- VECTOR SEARCH --------------------

  /**
   * Add documents to vector search.
   * @param {Object} params
   * @param {Array<{text: string, metadata?: Object}>} params.documents
   * @param {string} [params.collection='default']
   * @returns {Promise<Object>}
   */
  async vectorAdd({ documents, collection = 'default' }) {
    return this._post('/v1/vector/add', { documents, collection });
  }

  /**
   * Query vector search.
   * @param {Object} params
   * @param {string} params.query - Search query
   * @param {string} [params.collection='default']
   * @param {number} [params.topK=5]
   * @returns {Promise<Array>}
   */
  async vectorQuery({ query, collection = 'default', topK = 5 }) {
    const result = await this._post('/v1/vector/search', {
      query,
      collection,
      top_k: topK,
    });
    return result.results || [];
  }

  // -------------------- BLOCKS --------------------

  /**
   * List all available blocks.
   * @returns {Promise<Array>}
   */
  async listBlocks() {
    const result = await this._get('/v1/blocks');
    return result.blocks || [];
  }

  /**
   * Check API health.
   * @returns {Promise<Object>}
   */
  async health() {
    return this._get('/v1/health');
  }
}

export class ChatResponse {
  constructor(data) {
    this._data = data;
  }

  /** @returns {string} */
  get text() {
    return this._data.text || '';
  }

  /** @returns {number} */
  get tokensUsed() {
    return this._data.tokens_total || 0;
  }

  /** @returns {string} */
  get model() {
    return this._data.model || '';
  }

  /** @returns {string} */
  get provider() {
    return this._data.provider || '';
  }

  /** @returns {Object} */
  get raw() {
    return this._data;
  }

  toString() {
    return this.text;
  }
}

export class StreamChunk {
  constructor(data) {
    this._data = data;
  }

  /** @returns {string} */
  get text() {
    return this._data.text || '';
  }

  /** @returns {boolean} */
  get done() {
    return this._data.done || false;
  }

  toString() {
    return this.text;
  }
}

export { CerebrumClient as default };
