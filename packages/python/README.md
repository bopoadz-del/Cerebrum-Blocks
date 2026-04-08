# Cerebrum SDK

**Build AI Like Lego. 3 Lines of Code.**

Official Python SDK for [Cerebrum Blocks](https://cerebrumblocks.com) - the modular AI platform.

## Installation

```bash
pip install cerebrum-sdk
```

## Quickstart

```python
import asyncio
from cerebrum_sdk import Cerebrum

async def main():
    # Initialize with your API key
    client = Cerebrum(api_key="cb_your_key_here")
    
    # Simple chat
    response = await client.chat("Explain quantum computing in simple terms")
    print(response.text)
    
    # Streaming chat
    async for chunk in client.chat.stream("Tell me a story about AI"):
        print(chunk.text, end="", flush=True)

asyncio.run(main())
```

## Get Your API Key

1. Sign up at [cerebrumblocks.com/dashboard](https://cerebrumblocks.com/dashboard)
2. Create a new API key
3. Set it as `CEREBRUM_API_KEY` or pass to `Cerebrum(api_key="...")`

## Features

- **16 AI Blocks**: Chat, PDF, OCR, Voice, Vector Search, Image, Translate, Code, Web, and more
- **Streaming**: Real-time token-by-token responses
- **Chaining**: Compose blocks into powerful pipelines
- **Type-Safe**: Full type hints and IDE autocomplete
- **Async**: Modern async/await patterns throughout

## Examples

### Chain Blocks Together

```python
from cerebrum_sdk import Cerebrum, chain

client = Cerebrum(api_key="cb_your_key")

# PDF → OCR → Chat = Document AI
result = await chain(client) \
    .then("pdf", {"extract": "text"}) \
    .then("ocr", {"lang": "eng"}) \
    .then("chat", {"prompt": "Extract invoice data:"}) \
    .run("invoice.pdf")

print(result.final_output)
```

### Vector Search

```python
# Add documents
await client.vector_add([
    {"text": "Cerebrum is an AI platform", "metadata": {"source": "docs"}},
    {"text": "Build AI like Lego blocks", "metadata": {"source": "blog"}}
], collection="knowledge")

# Search
results = await client.vector_search("How to build AI?", top_k=3)
for doc in results:
    print(f"{doc['score']:.2f}: {doc['text']}")
```

### Execute Any Block

```python
# OCR on an image
result = await client.execute("ocr", "image.png", {"lang": "eng"})
print(result["text"])

# Translate text
result = await client.execute("translate", "Hello world", {"target": "es"})
print(result["text"])
```

## Documentation

- [Full Documentation](https://docs.cerebrumblocks.com)
- [API Reference](https://docs.cerebrumblocks.com/api)
- [Examples](https://github.com/bopoadz-del/cerebrum-blocks/tree/main/examples)

## License

MIT License - see [LICENSE](LICENSE) for details.
