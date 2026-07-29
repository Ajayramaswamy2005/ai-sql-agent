from pydantic import BaseModel, Field
from typing import Any


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question to convert to SQL")
    session_id: str = Field(default="default", description="Session ID for conversation memory")


class QueryResponse(BaseModel):
    session_id: str
    user_query: str
    generated_sql: str
    answer: str
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0
    success: bool
    retry_count: int = 0
    error: str | None = None


class SchemaResponse(BaseModel):
    tables: list[str]
    schema_info: str


class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    model: str
