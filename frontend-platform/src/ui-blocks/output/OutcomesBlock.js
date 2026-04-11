import { UIBlock, registerBlock } from '../../blocks/UIBlock.js';

// OutcomesBlock - Displays structured results (construction metrics, etc.)
class OutcomesBlock extends UIBlock {
  constructor(config = {}) {
    super({
      name: 'outcomes',
      layer: 3,
      tags: ['output', 'ui'],
      requires: []
    });
    this.outcomes = [];
    this.onOutcomeCallback = config.onOutcome || (() => {});
  }

  async process(data, params = {}) {
    const { type = 'add' } = params;

    switch (type) {
      case 'add':
        return this.addOutcome(data, params);
      case 'clear':
        return this.clearOutcomes();
      case 'update':
        return this.updateOutcome(data.id, data);
      default:
        throw new Error(`Unknown outcome action: ${type}`);
    }
  }

  addOutcome(data, params = {}) {
    const outcome = {
      id: data.id || Date.now(),
      type: params.category || 'general',
      project: data.project || 'Unknown',
      timestamp: new Date(),
      data: data,
      
      // Construction-specific fields
      ...(data.floor_area && { area: data.floor_area }),
      ...(data.concrete_volume && { concrete: data.concrete_volume }),
      ...(data.steel_weight && { steel: data.steel_weight }),
      ...(data.estimated_cost && { cost: data.estimated_cost }),
      
      // Generic display
      title: data.title || params.title,
      summary: data.summary || params.summary,
      details: data.details || {}
    };

    this.outcomes.unshift(outcome);
    this.onOutcomeCallback(outcome);
    this.emit('outcome:add', outcome);

    return outcome;
  }

  // Parse chain result and extract construction outcomes
  parseConstructionResult(result) {
    const outcomes = [];

    // Check for construction block output
    if (result.results) {
      const constructionResult = result.results.find(
        r => r.block === 'construction'
      );

      if (constructionResult?.result?.quantities) {
        const q = constructionResult.result.quantities;
        outcomes.push({
          type: 'construction',
          area: q.floor_area_sqm,
          concrete: q.concrete_volume_m3,
          steel: q.steel_weight_kg,
          confidence: q.confidence || 0.85
        });
      }
    }

    // Check for AI estimate
    if (result.final_output?.ai_estimate) {
      const est = result.final_output.ai_estimate;
      outcomes.push({
        type: 'estimate',
        cost: est.total,
        currency: est.currency || 'USD'
      });
    }

    return outcomes;
  }

  updateOutcome(id, updates) {
    const index = this.outcomes.findIndex(o => o.id === id);
    if (index >= 0) {
      this.outcomes[index] = { ...this.outcomes[index], ...updates };
      this.emit('outcome:update', this.outcomes[index]);
      return this.outcomes[index];
    }
    return null;
  }

  clearOutcomes() {
    this.outcomes = [];
    this.emit('outcomes:clear');
    return { cleared: true };
  }

  getOutcomes(category = null) {
    if (category) {
      return this.outcomes.filter(o => o.type === category);
    }
    return this.outcomes;
  }

  getLatest() {
    return this.outcomes[0] || null;
  }
}

registerBlock('outcomes', OutcomesBlock);
export default OutcomesBlock;
