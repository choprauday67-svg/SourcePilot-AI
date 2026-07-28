"""
Phase 2 — Comment Pydantic Schemas (Team Collaboration)
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class CommentCreate(BaseModel):
    body: str
    mentions: Optional[List[str]] = []  # List of user IDs to @mention


class CommentResponse(BaseModel):
    id: str
    requirement_id: str
    author_id: str
    body: str
    mentions: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentUpdate(BaseModel):
    body: str
