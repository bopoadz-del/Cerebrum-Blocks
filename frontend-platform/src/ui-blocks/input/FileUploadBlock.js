import { UIBlock, registerBlock } from '../../blocks/UIBlock.js';

// FileUploadBlock - Handles file uploads with automatic routing
class FileUploadBlock extends UIBlock {
  constructor(config = {}) {
    super({
      name: 'file_upload',
      layer: 2,
      tags: ['input', 'file'],
      requires: ['api', 'chain']
    });
    this.api = config.api;
    this.chain = config.chain;
    this.acceptedTypes = config.acceptedTypes || ['*/*'];
    this.maxSize = config.maxSize || 50 * 1024 * 1024; // 50MB
  }

  async process(file, params = {}) {
    if (!file) {
      throw new Error('No file provided');
    }

    // Validate file
    this.validateFile(file);

    this.emit('upload:start', { 
      file: file.name, 
      size: file.size,
      type: file.type 
    });

    try {
      // 1. Upload file via API
      const uploadResult = await this.api.uploadFile(file);
      
      this.emit('upload:complete', { 
        url: uploadResult.url,
        file: file.name 
      });

      // 2. If we have text context, include it
      const input = params.text 
        ? { url: uploadResult.url, text: params.text }
        : uploadResult.url;

      // 3. Execute chain with auto-routing
      const chainResult = await this.chain.execute(input, {
        file,
        autoRoute: true
      });

      return {
        upload: uploadResult,
        chain: chainResult
      };

    } catch (error) {
      this.emit('upload:error', { error: error.message });
      throw error;
    }
  }

  validateFile(file) {
    // Check size
    if (file.size > this.maxSize) {
      throw new Error(`File too large. Max size: ${this.maxSize / 1024 / 1024}MB`);
    }

    // Check type
    if (this.acceptedTypes[0] !== '*/*') {
      const isAccepted = this.acceptedTypes.some(type => {
        if (type.endsWith('/*')) {
          return file.type.startsWith(type.replace('/*', ''));
        }
        return file.type === type;
      });

      if (!isAccepted) {
        throw new Error(`File type not accepted. Allowed: ${this.acceptedTypes.join(', ')}`);
      }
    }
  }

  // Quick action handlers
  async analyzeFloorplan(file) {
    return this.process(file, {
      text: 'Analyze this floorplan and calculate material costs'
    });
  }

  async extractMeasurements(file) {
    return this.process(file, {
      text: 'Extract all measurements from this drawing'
    });
  }

  async checkCompliance(file) {
    return this.process(file, {
      text: 'Check this blueprint for Saudi building code compliance'
    });
  }

  async translateDocument(file, targetLang = 'arabic') {
    return this.process(file, {
      text: `Translate this document to ${targetLang}`
    });
  }
}

registerBlock('file_upload', FileUploadBlock);
export default FileUploadBlock;
