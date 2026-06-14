"""Shared API response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Service liveness and version response."""

    status: str = "ok"
    project: str
    version: str


class MessageResponse(BaseModel):
    """Generic response for operations that are still placeholders."""

    status: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
