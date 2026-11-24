from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Overall application health status")
    version: str = Field(..., description="DockScope version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str = Field(..., description="Deployment environment")


class ReadyResponse(BaseModel):
    status: str = Field(default="ready", description="Service readiness status")
    database: str = Field(default="connected", description="Database connection status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
