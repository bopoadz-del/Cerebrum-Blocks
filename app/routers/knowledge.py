"""Knowledge Router — RAG question-answering endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import require_api_key, get_block_instance

router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(..., description="Question to ask the knowledge base")
    collections: Optional[List[str]] = Field(default=None, description="Vector collections to search")
    top_k: int = Field(default=5, ge=1, le=20)
    llm_provider: Optional[str] = Field(default=None, description="Override default LLM")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    collections: Optional[List[str]] = Field(default=None)
    top_k: int = Field(default=5, ge=1, le=20)


class SummarizeRequest(BaseModel):
    collection: str = Field(default="cerebrum_captures")
    n_docs: int = Field(default=10, ge=1, le=50)
    llm_provider: Optional[str] = Field(default=None)


@router.post("/knowledge/ask")
async def knowledge_ask(request: AskRequest, auth: dict = Depends(require_api_key)):
    """Ask a question — RAG retrieval + LLM synthesis with citations."""
    block = get_block_instance("knowledge")
    result = await block.process(
        request.question,
        {
            "action": "ask",
            "collections": request.collections,
            "top_k": request.top_k,
            "llm_provider": request.llm_provider,
        },
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("error", "Ask failed"))

    return result.get("result", result)


@router.post("/knowledge/search")
async def knowledge_search(request: SearchRequest, auth: dict = Depends(require_api_key)):
    """Search knowledge base without LLM synthesis."""
    block = get_block_instance("knowledge")
    result = await block.process(
        request.query,
        {
            "action": "search",
            "collections": request.collections,
            "top_k": request.top_k,
        },
    )
    return result.get("result", result)


@router.post("/knowledge/summarize")
async def knowledge_summarize(request: SummarizeRequest, auth: dict = Depends(require_api_key)):
    """Summarize recent documents in a collection."""
    block = get_block_instance("knowledge")
    result = await block.process(
        None,
        {
            "action": "summarize",
            "collection": request.collection,
            "n_docs": request.n_docs,
            "llm_provider": request.llm_provider,
        },
    )
    return result.get("result", result)
