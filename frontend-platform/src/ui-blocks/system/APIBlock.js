import { UIBlock, registerBlock } from '../../blocks/UIBlock.js';

const API_BASE = 'https://ssdppg.onrender.com';

class APIBlock extends UIBlock {
  constructor(config = {}) {
    super({ 
      name: 'api', 
      layer: 0, 
      tags: ['system', 'api'],
      requires: []
    });
    this.baseURL = config.endpoint || API_BASE;
    this.apiKey = localStorage.getItem('cerebrum_key') || 'cb_dev_key';
  }

  async process(input, params = {}) {
    const { action = 'execute', ...rest } = params;
    
    switch (action) {
      case 'execute':
        return this.executeBlock(input.block, input.input, input.params);
      case 'chain':
        return this.executeChain(input.chain, input.input, input.params);
      case 'upload':
        return this.uploadFile(input);
      case 'health':
        return this.healthCheck();
      default:
        throw new Error(`Unknown API action: ${action}`);
    }
  }

  // Execute single backend block
  async executeBlock(blockName, input, params = {}) {
    const response = await fetch(`${this.baseURL}/v1/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({ block: blockName, input, params })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API error: ${response.status}`);
    }
    
    return await response.json();
  }

  // Execute chain of blocks
  async executeChain(chain, input, params = {}) {
    const response = await fetch(`${this.baseURL}/v1/chain`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({ chain, input, params })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API error: ${response.status}`);
    }
    
    return await response.json();
  }

  // Upload file to storage
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseURL}/v1/upload`, {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Upload error: ${response.status}`);
    }
    
    return await response.json();
  }

  // Health check
  async healthCheck() {
    const response = await fetch(`${this.baseURL}/health`);
    return response.ok;
  }

  // Get available blocks from backend
  async getBlocks() {
    const response = await fetch(`${this.baseURL}/v1/blocks`, {
      headers: { 'Authorization': `Bearer ${this.apiKey}` }
    });
    return await response.json();
  }
}

registerBlock('api', APIBlock);
export default APIBlock;
