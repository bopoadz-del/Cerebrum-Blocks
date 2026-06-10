"""Medical domain types — FHIR-aligned normalised models.

Copied from ``block_store/kits/medical/types.py`` on kit install
(see manifest ``skeleton_artifacts``).
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Patient(BaseModel):
    id: str
    name: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    identifiers: List[dict[str, str]] = Field(default_factory=list)


class Observation(BaseModel):
    id: str
    patient_id: str
    code: Optional[str] = None
    display: Optional[str] = None
    value: Optional[Any] = None
    unit: Optional[str] = None
    effective_date: Optional[str] = None
    status: Optional[str] = None


class MedicationRequest(BaseModel):
    id: str
    patient_id: str
    medication: Optional[str] = None
    dosage: Optional[str] = None
    status: Optional[str] = None
    authored_on: Optional[str] = None
