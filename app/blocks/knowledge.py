"""RAG Knowledge Block v2 — Ask questions across all stored captures and swarm runs.

Retrieval-Augmented Generation:
  Question → Vector search → Top-k chunks → LLM synthesis → Cited answer
"""

import os
import json
from typing import Any, Dict, List, Optional

from app.core.universal_base import UniversalBlock
from app.core.typed_block import TypedBlock, Schema, ContentType


class KnowledgeBlock(TypedBlock):
    """Knowledge retrieval and synthesis engine."""

    name = "knowledge"
    version = "2.0.0"
    description = "Ask questions across stored captures and swarm runs using RAG"
    layer = 3
    tags = ["knowledge", "rag", "retrieval", "qa", "memory", "ai"]
    requires = ["vector_search"]

    input_schema = Schema(
        content_type=ContentType.TEXT,
        required_fields=["question"],
        optional_fields=["collections", "top_k", "llm_provider", "n_docs"],
        format_hints={}
    )

    output_schema = Schema(
        content_type=ContentType.JSON,
        required_fields=["status", "answer"],
        optional_fields=["sources", "confidence", "query", "chunks_retrieved"],
        format_hints={}
    )

    accepted_input_types = ["Text", "Question", "JSON"]
    produced_output_types = ["JSON", "Answer", "SearchResults"]


    async def execute(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        action = params.get("action") if isinstance(params, dict) else None
        if isinstance(input_data, str):
            input_data = {"question": input_data}
        return await super().execute(input_data, params)

    def validate_input(self, data: Any) -> Dict[str, Any]:
        if isinstance(data, dict) and data.get("action") in {"health", "status", "list", "history", "get", "unschedule", "broadcast", "search", "summarize", "structure", "execute_async"}:
            return {"valid": True, "errors": [], "warnings": [], "data": data}
        return super().validate_input(data)

    default_config = {
        "llm_provider": os.getenv("LLM_PROVIDER", "ollama"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "deepseek_model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "openrouter_model": os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        "vector_db_url": os.getenv("VECTOR_DB_URL", "http://localhost:8001"),
        "default_top_k": 5,
        "default_collections": ["cerebrum_captures", "cerebrum_swarm"],
    }

    ui_schema = {
        "input": {
            "type": "text",
            "placeholder": "Ask a question about your knowledge base...",
            "multiline": False,
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "answer", "type": "text", "label": "Answer"},
                {"name": "sources", "type": "json", "label": "Sources"},
                {"name": "confidence", "type": "percentage", "label": "Confidence"},
            ],
        },
        "quick_actions": [
            {"icon": "❓", "label": "Ask Question", "prompt": "Ask about your data"},
            {"icon": "🔍", "label": "Search Only", "prompt": "Search knowledge base"},
            {"icon": "📝", "label": "Summarize", "prompt": "Summarize recent captures"},
        ],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        action = params.get("action", "ask")

        if action == "ask":
            return await self._ask(input_data, params)
        elif action == "search":
            return await self._search_only(input_data, params)
        elif action == "summarize":
            return await self._summarize_collection(params)
        else:
            return {"status": "error", "error": f"Unknown action: {action}"}

    # ── Core RAG: Ask ──────────────────────────────────────────────────────────

    async def _ask(self, question: Any, params: Dict) -> Dict:
        query = question if isinstance(question, str) else str(question)
        collections = params.get("collections") or self.config.get("default_collections", ["cerebrum_captures"])
        top_k = params.get("top_k", self.config.get("default_top_k", 5))
        llm_provider = params.get("llm_provider", self.config.get("llm_provider", "ollama"))

        # 1. Retrieve from all collections
        all_chunks = []
        for collection in collections:
            results = await self._search_vectors(query, collection, top_k)
            for r in results:
                r["collection"] = collection
            all_chunks.extend(results)

        if not all_chunks:
            return {
                "status": "success",
                "answer": "I don't have any relevant information in my knowledge base.",
                "sources": [],
                "confidence": 0.0,
            }

        # 2. Deduplicate and rank
        all_chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_chunks = all_chunks[:top_k]

        # 3. Build context for LLM
        context_parts = []
        source_map = {}
        for idx, chunk in enumerate(top_chunks):
            doc_id = chunk.get("id", f"chunk_{idx}")
            text = chunk.get("text", chunk.get("document", ""))
            meta = chunk.get("metadata", {})
            context_parts.append(f"[Source {idx+1}] {text}")
            source_map[f"Source {idx+1}"] = {
                "id": doc_id,
                "collection": chunk.get("collection", "unknown"),
                "score": chunk.get("score", 0),
                "metadata": meta,
            }

        context = "\n\n".join(context_parts)

        # 4. Synthesize with LLM
        system_prompt = (
            "You are a knowledge synthesis engine. Answer the user's question "
            "using ONLY the provided sources. Cite sources as [Source N]. "
            "If the sources don't contain the answer, say so. Be concise."
        )
        user_prompt = f"""Question: {query}

Sources:
{context}

Answer the question and cite sources.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            answer_data = await self._llm_chat(messages, llm_provider)
            answer_text = answer_data.get("content", "")
        except Exception as e:
            # Fallback: return top chunk as answer
            answer_text = f"Based on my knowledge base:\n\n{top_chunks[0].get('text', '')}"

        # 5. Extract cited sources from answer
        cited_sources = self._extract_citations(answer_text, source_map)

        return {
            "status": "success",
            "answer": answer_text,
            "sources": cited_sources,
            "confidence": self._compute_confidence(top_chunks),
            "query": query,
            "chunks_retrieved": len(top_chunks),
        }

    # ── Search Only ────────────────────────────────────────────────────────────

    async def _search_only(self, query: Any, params: Dict) -> Dict:
        query_str = query if isinstance(query, str) else str(query)
        collections = params.get("collections") or self.config.get("default_collections", ["cerebrum_captures"])
        top_k = params.get("top_k", self.config.get("default_top_k", 5))

        all_results = []
        for collection in collections:
            results = await self._search_vectors(query_str, collection, top_k)
            for r in results:
                r["collection"] = collection
            all_results.extend(results)

        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return {
            "status": "success",
            "query": query_str,
            "results": all_results[:top_k],
            "total_found": len(all_results),
        }

    # ── Summarize Collection ───────────────────────────────────────────────────

    async def _summarize_collection(self, params: Dict) -> Dict:
        collection = params.get("collection", "cerebrum_captures")
        n_docs = params.get("n_docs", 10)
        llm_provider = params.get("llm_provider", self.config.get("llm_provider", "ollama"))

        # Get recent documents (query with empty string or list operation)
        docs = await self._list_collection_docs(collection, n_docs)
        if not docs:
            return {"status": "success", "summary": "No documents in collection.", "documents_summarized": 0}

        combined = "\n\n---\n\n".join([d.get("text", "")[:1000] for d in docs])
        messages = [
            {"role": "system", "content": "Summarize the following documents into 3-5 bullet points."},
            {"role": "user", "content": combined},
        ]

        try:
            result = await self._llm_chat(messages, llm_provider)
            summary = result.get("content", "")
        except Exception as e:
            summary = f"Failed to summarize: {e}"

        return {
            "status": "success",
            "summary": summary,
            "documents_summarized": len(docs),
            "collection": collection,
        }

    # ── Vector Search ──────────────────────────────────────────────────────────

    async def _search_vectors(self, query: str, collection: str, n_results: int) -> List[Dict]:
        vector_block = self.get_dep("vector_search")

        if vector_block:
            try:
                result = await vector_block.process(
                    query,
                    {"operation": "search", "collection": collection, "n_results": n_results},
                )
                if result.get("status") == "success":
                    return result.get("result", {}).get("results", [])
            except Exception:
                pass

        # Fallback HTTP
        import httpx
        db_url = self.config.get("vector_db_url", "")
        if not db_url:
            return []
        try:
            payload = {"collection": collection, "query": query, "n_results": n_results}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(f"{db_url}/api/v1/collections/query", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("results", [])
        except Exception:
            pass
        return []

    async def _list_collection_docs(self, collection: str, n: int) -> List[Dict]:
        """List recent documents from a collection."""
        vector_block = self.get_dep("vector_search")
        if vector_block:
            try:
                result = await vector_block.process(
                    None,
                    {"operation": "search", "collection": collection, "n_results": n},
                )
                if result.get("status") == "success":
                    return result.get("result", {}).get("results", [])
            except Exception:
                pass
        return []

    # ── LLM Routing ────────────────────────────────────────────────────────────

    async def _llm_chat(self, messages: List[Dict], provider: str) -> Dict:
        import httpx

        if provider == "ollama":
            url = f"{self.config.get('ollama_base_url')}/api/chat"
            payload = {
                "model": self.config.get("ollama_model", "llama3.2:3b"),
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.3},
            }
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {"content": data["message"]["content"]}

        elif provider == "deepseek":
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.get('deepseek_api_key')}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.config.get("deepseek_model", "deepseek-chat"),
                "messages": messages,
                "temperature": 0.3,
            }
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {"content": data["choices"][0]["message"]["content"]}

        elif provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.get('openrouter_api_key')}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.config.get("openrouter_model"),
                "messages": messages,
                "temperature": 0.3,
            }
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {"content": data["choices"][0]["message"]["content"]}
        else:
            raise ValueError(f"Unknown provider: {provider}")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _extract_citations(self, answer: str, source_map: Dict) -> List[Dict]:
        """Extract which sources were actually cited in the answer."""
        cited = []
        for label, meta in source_map.items():
            if label in answer:
                cited.append(meta)
        return cited

    def _compute_confidence(self, chunks: List[Dict]) -> float:
        if not chunks:
            return 0.0
        scores = [c.get("score", 0) for c in chunks if c.get("score") is not None]
        if not scores:
            return 0.5
        avg = sum(scores) / len(scores)
        return round(min(avg, 1.0), 2)

