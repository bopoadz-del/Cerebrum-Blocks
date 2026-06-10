"""Law & Legal Practice Suite domain types."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LawCase(BaseModel):
    case_id: str
    title: str
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    case_number: Optional[str] = None
    status: Optional[str] = None
    filed_date: Optional[str] = None
    parties: List[str] = Field(default_factory=list)


class CourtFiling(BaseModel):
    filing_id: str
    case_id: str
    document_type: str
    filed_date: Optional[str] = None
    docket_number: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
