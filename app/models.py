from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class FileEdit(BaseModel):
    file_path: str
    original_hash: str
    unified_diff: str


class AgentPlan(BaseModel):
    edits: List[FileEdit]


class AgentRequest(BaseModel):
    repo_url: str
    prompt: str


class AgentSessionOut(BaseModel):
    id: str
    created_at: datetime
    repo_url: str
    prompt: str
    files_changed: List[str]
    status: str
    duration_sec: Optional[float]
    error: Optional[str]

    class Config:
        from_attributes = True
