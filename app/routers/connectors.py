"""Connector routers — direct invoke endpoints for domain connectors."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.http_errors import classify_block_error
from app.dependencies import get_block_instance, require_api_key

router = APIRouter(prefix="/v1/connectors", tags=["connectors"])


class EHRFetchRequest(BaseModel):
    resource: str = Field(default="Patient", description="Patient | Observation | MedicationRequest")
    resource_id: Optional[str] = None
    patient_id: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    action: str = "fetch"


@router.post("/medical/ehr")
async def medical_ehr_invoke(
    request: EHRFetchRequest,
    auth: dict = Depends(require_api_key),
):
    """Direct invoke for the FHIR medical EHR connector."""
    block = get_block_instance("medical_ehr_connector")
    params = {"action": request.action, "resource": request.resource}
    data = request.model_dump(exclude_none=True)
    result = await block.process(data, params)

    if result.get("status") == "error":
        err = result.get("error", "EHR fetch failed")
        raise HTTPException(status_code=classify_block_error(err), detail=err)

    return result
