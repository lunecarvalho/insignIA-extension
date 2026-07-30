from pydantic import BaseModel
from typing import List, Optional, Any


class Message(BaseModel):
    role: Optional[str]
    text: str
    timestamp: Optional[Any]


class ConversationCreate(BaseModel):
    id: Optional[str]
    url: Optional[str]
    messages: List[Message]
