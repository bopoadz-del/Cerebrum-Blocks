import { UIBlock, registerBlock } from '../../blocks/UIBlock.js';

// ChatInputBlock - Handles text input with smart routing
class ChatInputBlock extends UIBlock {
  constructor(config = {}) {
    super({
      name: 'chat_input',
      layer: 2,
      tags: ['input', 'chat'],
      requires: ['api', 'chain']
    });
    this.api = config.api;
    this.chain = config.chain;
    this.history = [];
  }

  async process(text, params = {}) {
    if (!text || !text.trim()) {
      throw new Error('Empty input');
    }

    this.emit('input:start', { text });

    // Add to history
    this.history.push({ role: 'user', content: text });

    try {
      // Execute chain with auto-routing
      const result = await this.chain.execute(text, { autoRoute: true });

      // Extract final output
      const response = result.final_output?.completion 
        || result.final_output?.text 
        || result.final_output 
        || 'No response';

      // Add to history
      this.history.push({ role: 'assistant', content: response });

      this.emit('input:complete', { 
        text,
        response,
        chain: result.chain
      });

      return {
        text,
        response,
        chain: result.chain,
        results: result.results
      };

    } catch (error) {
      this.emit('input:error', { text, error: error.message });
      throw error;
    }
  }

  // Send with file context (for when user uploads then types)
  async sendWithContext(text, fileUrl, fileType) {
    const input = fileUrl 
      ? { url: fileUrl, text }
      : text;

    const params = fileType ? { file: { type: fileType } } : {};
    
    return this.process(input, params);
  }

  // Quick action: Search knowledge base
  async searchKnowledge(query) {
    this.emit('input:start', { text: query, type: 'vector_search' });

    try {
      // Call ZVec block directly
      const searchResult = await this.api.executeBlock('zvec', {
        action: 'search',
        query: query,
        top_k: 5
      });

      // Get context
      const context = searchResult.results 
        ? searchResult.results.map(r => r.text).join('\n---\n')
        : '';

      // Send to AI with context
      const prompt = context 
        ? `Based on previous documents:\n${context}\n\nUser question: ${query}`
        : query;

      const chatResult = await this.api.executeBlock('ai_core', prompt, {
        action: 'chat',
        provider: 'deepseek'
      });

      return {
        query,
        context,
        response: chatResult.completion || chatResult
      };

    } catch (error) {
      this.emit('input:error', { query, error: error.message });
      throw error;
    }
  }

  // Get conversation history
  getHistory() {
    return this.history;
  }

  // Clear history
  clear() {
    this.history = [];
    this.emit('history:clear');
  }
}

registerBlock('chat_input', ChatInputBlock);
export default ChatInputBlock;
