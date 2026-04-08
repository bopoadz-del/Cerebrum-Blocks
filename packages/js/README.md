# Cerebrum JS

**Build AI Like Lego. 3 Lines of Code.**

Official JavaScript/TypeScript SDK for [Cerebrum Blocks](https://cerebrumblocks.com) - the modular AI platform.

Works in Node.js, browsers, and edge runtimes.

## Installation

```bash
npm install cerebrum-js
```

## Quickstart

```javascript
import { Cerebrum } from 'cerebrum-js';

// Initialize with your API key
const client = new Cerebrum({ apiKey: 'cb_your_key_here' });

// Simple chat
const response = await client.chat('Explain quantum computing in simple terms');
console.log(response.text);

// Streaming chat
for await (const chunk of client.chatStream('Tell me a story about AI')) {
  process.stdout.write(chunk.text);
}
```

## Get Your API Key

1. Sign up at [cerebrumblocks.com/dashboard](https://cerebrumblocks.com/dashboard)
2. Create a new API key
3. Set it as `CEREBRUM_API_KEY` env var or pass to constructor

## Features

- **16 AI Blocks**: Chat, PDF, OCR, Voice, Vector Search, Image, Translate, Code, Web, and more
- **Streaming**: Real-time token-by-token responses
- **Chaining**: Compose blocks into powerful pipelines
- **TypeScript**: Full type safety and IDE autocomplete
- **Universal**: Works in Node.js, browsers, Deno, and edge runtimes

## Examples

### Chain Blocks Together

```javascript
import { Cerebrum, chain } from 'cerebrum-js';

const client = new Cerebrum({ apiKey: 'cb_your_key' });

// PDF → OCR → Chat = Document AI
const result = await chain(client)
  .then('pdf', { extract: 'text' })
  .then('ocr', { lang: 'eng' })
  .then('chat', { prompt: 'Extract invoice data:' })
  .run('invoice.pdf');

console.log(result.finalOutput);
```

### Vector Search

```javascript
// Add documents
await client.vectorAdd([
  { text: 'Cerebrum is an AI platform', metadata: { source: 'docs' } },
  { text: 'Build AI like Lego blocks', metadata: { source: 'blog' } }
], 'knowledge');

// Search
const results = await client.vectorSearch('How to build AI?', 'knowledge', 3);
for (const doc of results) {
  console.log(`${doc.score.toFixed(2)}: ${doc.text}`);
}
```

### Execute Any Block

```javascript
// OCR on an image
const result = await client.execute('ocr', 'image.png', { lang: 'eng' });
console.log(result.text);

// Translate text
const result = await client.execute('translate', 'Hello world', { target: 'es' });
console.log(result.text);
```

### TypeScript

```typescript
import { Cerebrum, ChatResponse, StreamChunk } from 'cerebrum-js';

const client = new Cerebrum({ apiKey: process.env.CEREBRUM_API_KEY! });

// Fully typed responses
const response: ChatResponse = await client.chat('Hello!');
console.log(response.text);

// Streaming with types
for await (const chunk of client.chatStream('Tell me more')) {
  const typedChunk: StreamChunk = chunk;
  process.stdout.write(typedChunk.text);
}
```

## Error Handling

```javascript
import { Cerebrum, AuthenticationError, RateLimitError } from 'cerebrum-js';

try {
  const response = await client.chat('Hello!');
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof RateLimitError) {
    console.error('Rate limit exceeded - upgrade your plan');
  } else {
    console.error('Error:', error.message);
  }
}
```

## Documentation

- [Full Documentation](https://docs.cerebrumblocks.com)
- [API Reference](https://docs.cerebrumblocks.com/api)
- [Examples](https://github.com/bopoadz-del/cerebrum-blocks/tree/main/examples)

## License

MIT License - see [LICENSE](LICENSE) for details.
