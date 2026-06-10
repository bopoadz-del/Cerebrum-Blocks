"""Video ingest router — POST /v1/video/ingest."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.http_errors import classify_block_error
from app.dependencies import get_block_instance, require_api_key

router = APIRouter(prefix="/v1/video", tags=["video"])


class ZoneOccupancyIn(BaseModel):
    zone_id: str
    label: Optional[str] = None
    count: int = 0
    capacity: Optional[int] = None
    occupancy_pct: Optional[float] = None


class QueueInfoIn(BaseModel):
    queue_id: str
    label: Optional[str] = None
    length: int = 0
    avg_wait_seconds: Optional[float] = None
    threshold_exceeded: bool = False


class AnomalyIn(BaseModel):
    anomaly_type: str
    severity: str = "medium"
    zone_id: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    description: Optional[str] = None


class VideoIngestRequest(BaseModel):
    source_id: str = "api"
    camera_id: str
    frame_id: Optional[str] = None
    zones: List[ZoneOccupancyIn] = Field(default_factory=list)
    queues: List[QueueInfoIn] = Field(default_factory=list)
    anomalies: List[AnomalyIn] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    auto_trigger: bool = True
    notify_channel: Optional[str] = None
    notify_to: Optional[str] = None


@router.post("/ingest")
async def video_ingest(
    request: VideoIngestRequest,
    auth: dict = Depends(require_api_key),
):
    """Ingest video analytics metadata; optionally chain anomaly trigger."""
    ingest = get_block_instance("video_metadata_ingest")
    payload = request.model_dump()
    result = await ingest.process(payload, {"action": "ingest"})

    if result.get("status") == "error":
        err = result.get("error", "Ingest failed")
        raise HTTPException(status_code=classify_block_error(err), detail=err)

    if result.get("trigger_recommended") and request.auto_trigger:
        trigger = get_block_instance("video_anomaly_trigger")
        if trigger is not None:
            trigger_data = {
                "metadata": payload,
                "channel": request.notify_channel or "webhook",
                "to": request.notify_to,
                "url": request.notify_to,
            }
            trigger_result = await trigger.process(trigger_data, {"action": "evaluate"})
            result["trigger"] = trigger_result

    return result
