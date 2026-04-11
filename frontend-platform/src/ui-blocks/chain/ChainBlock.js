import { UIBlock, registerBlock } from '../../blocks/UIBlock.js';

// ChainBlock - Orchestrates execution of multiple blocks in sequence
class ChainBlock extends UIBlock {
  constructor(config = {}) {
    super({
      name: 'chain',
      layer: 1,
      tags: ['chain', 'orchestrator'],
      requires: ['api']
    });
    this.api = config.api;
    this.activeChain = [];
    this.currentStep = 0;
  }

  async process(input, params = {}) {
    const { chain, autoRoute = false } = params;
    
    // Auto-determine chain based on input
    const blocksToExecute = autoRoute 
      ? this.determineChain(input, params.file)
      : chain;

    if (!blocksToExecute || blocksToExecute.length === 0) {
      throw new Error('No blocks specified for chain execution');
    }

    this.activeChain = blocksToExecute.map(b => typeof b === 'string' ? b : b.name);
    this.currentStep = 0;

    // Emit chain start event
    this.emit('chain:start', { 
      chain: this.activeChain,
      display: blocksToExecute.map(b => this.getDisplayName(typeof b === 'string' ? b : b.name))
    });

    let currentInput = input;
    const results = [];

    // Execute each block in sequence
    for (let i = 0; i < blocksToExecute.length; i++) {
      this.currentStep = i;
      const blockName = typeof blocksToExecute[i] === 'string' 
        ? blocksToExecute[i] 
        : blocksToExecute[i].name;
      const blockParams = typeof blocksToExecute[i] === 'string' 
        ? {} 
        : blocksToExecute[i].params || {};

      this.emit('step:start', { 
        step: i + 1, 
        total: blocksToExecute.length,
        block: blockName,
        display: this.getDisplayName(blockName)
      });

      try {
        const result = await this.api.executeBlock(blockName, currentInput, blockParams);
        results.push({ block: blockName, result });
        
        // Output of this block becomes input of next
        currentInput = result.result || result;

        this.emit('step:complete', { 
          step: i + 1, 
          block: blockName,
          result
        });
      } catch (error) {
        this.emit('step:error', { 
          step: i + 1, 
          block: blockName, 
          error: error.message 
        });
        throw error;
      }
    }

    this.emit('chain:complete', { 
      chain: this.activeChain,
      results,
      finalOutput: currentInput
    });

    return {
      chain: this.activeChain,
      results,
      final_output: currentInput
    };
  }

  // Smart routing - determines which blocks to call based on input
  determineChain(text, file) {
    const isPDF = file?.type === 'application/pdf';
    const isImage = file?.type?.startsWith('image/');
    const isAudio = file?.type?.startsWith('audio/');
    const text_lower = (text || '').toLowerCase();
    
    const isConstruction = /concrete|steel|measurement|area|cost|bim|floorplan|masonry|blueprint|rebar|formwork/i.test(text_lower);
    const isCode = /code|function|program|script|python|javascript/i.test(text_lower);
    const isSearch = /search|find|look up|google/i.test(text_lower);
    const isTranslate = /translate|arabic|english|french/i.test(text_lower);
    const isImageAnalysis = /image|photo|picture|analyze.*image/i.test(text_lower);
    const isVoice = isAudio || /voice|speak|audio|record/i.test(text_lower);
    const isVector = /previous.*doc|past.*project|similar.*file|knowledge base/i.test(text_lower);

    // File-based routing
    if (file && isPDF && isConstruction) {
      return ['pdf', 'construction', 'ai_core'];
    }
    if (file && isPDF) {
      return ['pdf', 'ocr', 'ai_core'];
    }
    if (file && isImage) {
      return ['ocr', 'ai_core'];
    }
    if (file && isAudio) {
      return ['voice', 'ai_core'];
    }

    // Text-based routing
    if (isCode) return ['code', 'ai_core'];
    if (isSearch) return ['search', 'ai_core'];
    if (isTranslate) return ['translate', 'ai_core'];
    if (isImageAnalysis) return ['image', 'ai_core'];
    if (isVoice) return ['voice', 'ai_core'];
    if (isVector) return ['zvec', 'ai_core'];

    // Default: Direct to AI Core
    return ['ai_core'];
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
      'zvec': 'Vector Search',
      'security': 'Security'
    };
    return names[blockName] || blockName;
  }

  getActiveChain() {
    return this.activeChain;
  }
}

registerBlock('chain', ChainBlock);
export default ChainBlock;
