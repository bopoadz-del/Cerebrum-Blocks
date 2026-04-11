// Base class for all UI blocks - mirrors backend UniversalBlock
export class UIBlock {
  constructor(config = {}) {
    this.name = config.name || 'unknown';
    this.layer = config.layer || 0;
    this.tags = config.tags || [];
    this.requires = config.requires || [];
    this.config = config;
    this.state = {};
    this.listeners = {};
  }

  // Execute block processing
  async process(input, params = {}) {
    throw new Error(`Block ${this.name} must implement process()`);
  }

  // Main execute wrapper with timing and error handling
  async execute(input, params = {}) {
    const start = Date.now();
    try {
      const result = await this.process(input, params);
      this.emit('complete', { block: this.name, result, time: Date.now() - start });
      return {
        block: this.name,
        status: 'success',
        result,
        processing_time_ms: Date.now() - start
      };
    } catch (error) {
      this.emit('error', { block: this.name, error: error.message });
      return {
        block: this.name,
        status: 'error',
        error: error.message,
        processing_time_ms: Date.now() - start
      };
    }
  }

  // Event system for block communication
  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
}

// Block registry
export const UI_BLOCK_REGISTRY = {};

export function registerBlock(name, BlockClass) {
  UI_BLOCK_REGISTRY[name] = BlockClass;
}

export function createBlock(name, config = {}) {
  const BlockClass = UI_BLOCK_REGISTRY[name];
  if (!BlockClass) throw new Error(`Block ${name} not found in registry`);
  return new BlockClass(config);
}
