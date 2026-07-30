from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class Reason(BaseModel):
    category: str
    subcategory: str
    confidence: int


class Sentiment(BaseModel):
    score: float
    label: str


class Quality(BaseModel):
    score: int
    checklist: Dict[str, bool]
    notes: Optional[str]


class AnalysisResult(BaseModel):
    reason: Reason
    sentiment: Sentiment
    quality: Quality
    trends: Dict[str, int]
    insights: List[str]
