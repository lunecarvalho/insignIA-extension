from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..db.session import Base


class Analysis(Base):
    __tablename__ = 'analyses'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    reason = Column(JSONB, nullable=False)
    sentiment = Column(JSONB, nullable=False)
    quality = Column(JSONB, nullable=False)
    trends = Column(JSONB, nullable=True)
    insights = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
