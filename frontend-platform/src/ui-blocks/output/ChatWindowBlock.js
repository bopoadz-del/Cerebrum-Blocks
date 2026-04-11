import { UIBlock, registerBlock } from '../../blocks/UIBlock.js';

// ChatWindowBlock - Manages the chat UI and message display
class ChatWindowBlock extends UIBlock {
  constructor(config = {}) {
    super({
      name: 'chat_window',
      layer: 3,
      tags: ['output', 'ui'],
      requires: []
    });
    this.messages = [];
    this.onMessageCallback = config.onMessage || (() => {});
    this.onChainCallback = config.onChain || (() => {});
  }

  async process(message, params = {}) {
    const { type = 'add', ...rest } = params;

    switch (type) {
      case 'add':
        return this.addMessage(message, rest);
      case 'update':
        return this.updateMessage(message.id, message);
      case 'clear':
        return this.clearMessages();
      case 'show_chain':
        return this.showChainIndicator(message);
      case 'hide_chain':
        return this.hideChainIndicator();
      default:
        throw new Error(`Unknown chat action: ${type}`);
    }
  }

  addMessage(content, params = {}) {
    const message = {
      id: Date.now() + Math.random(),
      role: params.role || 'assistant',
      content,
      timestamp: new Date(),
      showActions: params.showActions || false,
      chain: params.chain || null
    };

    this.messages.push(message);
    this.onMessageCallback(message);
    this.emit('message:add', message);

    return message;
  }

  updateMessage(id, updates) {
    const index = this.messages.findIndex(m => m.id === id);
    if (index >= 0) {
      this.messages[index] = { ...this.messages[index], ...updates };
      this.emit('message:update', this.messages[index]);
      return this.messages[index];
    }
    return null;
  }

  clearMessages() {
    this.messages = [];
    this.emit('messages:clear');
    return { cleared: true };
  }

  showChainIndicator(chain) {
    const indicator = {
      active: true,
      chain,
      display: chain.map(b => this.getDisplayName(b)).join(' → ')
    };
    
    this.onChainCallback(indicator);
    this.emit('chain:show', indicator);
    
    return indicator;
  }

  hideChainIndicator() {
    this.onChainCallback({ active: false });
    this.emit('chain:hide');
    return { active: false };
  }

  getDisplayName(blockName) {
    const names = {
      'pdf': 'PDF Extractor',
      'ocr': 'OCR Vision',
      'construction': 'Construction AI',
      'ai_core': 'AI Core',
      'chat': 'Chat',
      'voice': 'Voice',
      'image': 'Image AI',
      'code': 'Code',
      'search': 'Search',
      'translate': 'Translate',
      'zvec': 'Vector Search'
    };
    return names[blockName] || blockName;
  }

  getMessages() {
    return this.messages;
  }

  getLastMessage() {
    return this.messages[this.messages.length - 1];
  }
}

registerBlock('chat_window', ChatWindowBlock);
export default ChatWindowBlock;
