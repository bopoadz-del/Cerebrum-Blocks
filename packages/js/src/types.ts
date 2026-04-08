/**
 * Type definitions for Cerebrum SDK
 */

/** Options for chat requests */
export interface ChatOptions {
  /** Model to use (default: gpt-3.5-turbo) */
  model?: string;
  /** System prompt (default: "You are a helpful assistant.") */
  system?: string;
  /** Maximum tokens to generate (default: 1000) */
  maxTokens?: number;
  /** Sampling temperature 0-2 (default: 0.7) */
  temperature?: number;
  /** AI provider: openai, anthropic, groq (default: openai) */
  provider?: string;
}

/** Options for streaming chat */
export interface StreamOptions extends ChatOptions {}

/** Parameters for block execution */
export interface BlockParams {
  [key: string]: any;
}

/** A step in a chain */
export interface ChainStep {
  /** Block name */
  block: string;
  /** Block parameters */
  params?: BlockParams;
}

/** Usage statistics */
export interface UsageStats {
  /** Total requests made */
  totalRequests: number;
  /** Total tokens used */
  totalTokens: number;
  /** Average response time in ms */
  avgResponseTimeMs: number;
  /** Daily breakdown */
  dailyBreakdown: Array<{
    date: string;
    requests: number;
    tokens: number;
  }>;
  /** Usage limits */
  limits: {
    requests: number;
    tokens: number;
  };
}

/** Block information */
export interface BlockInfo {
  /** Block name */
  name: string;
  /** Block version */
  version: string;
  /** Block description */
  description: string;
  /** Whether block requires API key */
  requiresApiKey: boolean;
  /** Supported input types */
  supportedInputs: string[];
  /** Supported output types */
  supportedOutputs: string[];
}

/** Message for chat completions */
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

/** OpenAI-compatible chat completion request */
export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  max_tokens?: number;
  temperature?: number;
  stream?: boolean;
}

/** Document for vector search */
export interface VectorDocument {
  text: string;
  metadata?: Record<string, any>;
}

/** Vector search result */
export interface VectorResult {
  text: string;
  metadata: Record<string, any>;
  score: number;
}
