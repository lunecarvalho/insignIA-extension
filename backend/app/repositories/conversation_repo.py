from sqlalchemy.orm import Session
from ..models.conversation import Conversation


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict) -> Conversation:
        conv = Conversation(**payload)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get(self, conv_id: int) -> Conversation | None:
        return self.db.query(Conversation).filter(Conversation.id == conv_id).first()

    def list(self, limit: int = 100):
        return self.db.query(Conversation).order_by(Conversation.created_at.desc()).limit(limit).all()
