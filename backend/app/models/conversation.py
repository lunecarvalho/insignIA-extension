from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..db.session import Base


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=True)
    messages = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
