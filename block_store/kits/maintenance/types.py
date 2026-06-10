"""Maintenance & Facilities Suite domain types."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WorkOrder(BaseModel):
    work_order_id: str
    title: str
    status: str = "open"
    priority: str = "medium"
    asset_id: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[str] = None


class SensorReading(BaseModel):
    sensor_id: str
    metric: str
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    asset_id: Optional[str] = None
    location: Optional[str] = None
