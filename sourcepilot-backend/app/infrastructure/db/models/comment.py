"""
RequirementComment — Phase 2 Team Collaboration Model

Stores team discussion threads attached to procurement requirements.
Supports @mentions via the `mentions` JSON field (list of user IDs).
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.infrastructure.db.base import Base


class RequirementComment(Base):
    __tablename__ = "requirement_comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String, ForeignKey("procurement_requirements.id"), nullable=False, index=True)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    mentions = Column(JSON, default=list)  # List of mentioned user IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
