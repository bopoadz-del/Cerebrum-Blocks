/**
 * Chain builder for composing blocks
 */

import { Cerebrum } from './client';
import { ChainStep } from './types';

/** Result of a chain execution */
export class ChainResult {
  private _data: Record<string, any>;
  
  constructor(data: Record<string, any>) {
    this._data = data;
  }
  
  /** Whether all steps completed successfully */
  get success(): boolean {
    return this._data.status === 'success';
  }
  
  /** The final output from the chain */
  get finalOutput(): any {
    return this._data.final_output;
  }
  
  /** Number of steps that ran */
  get stepsExecuted(): number {
    return this._data.steps_executed || 0;
  }
  
  /** Total execution time in milliseconds */
  get totalTimeMs(): number {
    return this._data.total_time_ms || 0;
  }
  
  /** Detailed results from each step */
  get stepResults(): any[] {
    return this._data.step_results || [];
  }
  
  /** Raw response data */
  get raw(): Record<string, any> {
    return this._data;
  }
  
  toJSON(): Record<string, any> {
    return this._data;
  }
}

/** Builder for chaining multiple blocks together */
export class Chain {
  private client: Cerebrum;
  private steps: ChainStep[] = [];
  
  constructor(client: Cerebrum) {
    this.client = client;
  }
  
  /**
   * Add a block to the chain
   * @param block - Block name (chat, pdf, ocr, translate, etc.)
   * @param params - Parameters for this block
   * @returns Self for method chaining
   * 
   * @example
   * chain.then("pdf", { extract: "text" })
   * chain.then("chat", { prompt: "Summarize:" })
   */
  then(block: string, params?: Record<string, any>): Chain {
    this.steps.push({ block, params });
    return this;
  }
  
  /**
   * Execute the chain with initial input
   * @param initialInput - Starting input (file path, text, etc.)
   * @returns ChainResult with final_output and step_results
   */
  async run(initialInput: any): Promise<ChainResult> {
    const result = await this.client.chain(this.steps, initialInput);
    return new ChainResult(result);
  }
}

/**
 * Create a new chain builder
 * @param client - Cerebrum client instance
 * @returns Chain builder for composing blocks
 * 
 * @example
 * const result = await chain(client)
 *   .then("pdf", { extract: "text" })
 *   .then("chat", { prompt: "Summarize:" })
 *   .run("document.pdf");
 */
export function chain(client: Cerebrum): Chain {
  return new Chain(client);
}
