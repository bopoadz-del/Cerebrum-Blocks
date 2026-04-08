/**
 * Response classes for Cerebrum SDK
 */

/** Chat response from API */
export class ChatResponse {
  private _data: Record<string, any>;
  
  constructor(data: Record<string, any>) {
    this._data = data;
  }
  
  /** The generated text response */
  get text(): string {
    return this._data.text || '';
  }
  
  /** Model used for generation */
  get model(): string {
    return this._data.model || '';
  }
  
  /** AI provider used */
  get provider(): string {
    return this._data.provider || '';
  }
  
  /** Total tokens consumed */
  get tokensUsed(): number {
    return this._data.tokens_total || 0;
  }
  
  /** Why generation stopped */
  get finishReason(): string {
    return this._data.finish_reason || '';
  }
  
  /** Raw response data */
  get raw(): Record<string, any> {
    return this._data;
  }
  
  toString(): string {
    return this.text;
  }
  
  toJSON(): Record<string, any> {
    return this._data;
  }
}

/** A chunk from a streaming response */
export class StreamChunk {
  private _data: Record<string, any>;
  
  constructor(data: Record<string, any>) {
    this._data = data;
  }
  
  /** Text content of this chunk */
  get text(): string {
    return this._data.content || '';
  }
  
  /** Whether this is the final chunk */
  get done(): boolean {
    return this._data.done || false;
  }
  
  /** Raw chunk data */
  get raw(): Record<string, any> {
    return this._data;
  }
  
  toString(): string {
    return this.text;
  }
}
