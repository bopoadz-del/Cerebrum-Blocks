/**
 * Cerebrum JavaScript SDK
 * 
 * Build AI Like Lego. One API. 16 blocks.
 * 
 * @example
 * ```javascript
 * import { Cerebrum } from 'cerebrum-js';
 * 
 * const client = new Cerebrum({ apiKey: 'cb_your_key' });
 * 
 * // Simple chat
 * const response = await client.chat('Hello!');
 * console.log(response.text);
 * 
 * // Streaming chat
 * for await (const chunk of client.chat.stream('Tell me a story')) {
 *   process.stdout.write(chunk.text);
 * }
 * ```
 */

export { Cerebrum, CerebrumClient } from './client';
export { Chain, chain, ChainResult } from './chain';
export { ChatResponse, StreamChunk } from './response';
export {
  CerebrumError,
  AuthenticationError,
  RateLimitError,
  BlockNotFoundError,
  ExecutionError,
} from './errors';
export type {
  ChatOptions,
  StreamOptions,
  BlockParams,
  ChainStep,
  UsageStats,
  BlockInfo,
} from './types';
