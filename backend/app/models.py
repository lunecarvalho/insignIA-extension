from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, conlist, field_validator


class AnalyzeRequest(BaseModel):
    chat_id: str = Field(..., min_length=1, max_length=120)
    canal: str = Field(..., min_length=1, max_length=60)
    mensagens: conlist(str, min_length=1)

    @field_validator("mensagens")
    @classmethod
    def validate_messages(cls, value: List[str]) -> List[str]:
        cleaned_messages = []
        for item in value:
            cleaned = item.strip()
            if not cleaned:
                raise ValueError("Mensagens nao podem estar vazias.")
            cleaned_messages.append(cleaned)
        return cleaned_messages


class SentimentResult(BaseModel):
    label: Literal["Positivo", "Neutro", "Negativo"]
    score: float = Field(..., ge=0.0, le=1.0)


class CategoryResult(BaseModel):
    categoria: str
    score: float = Field(..., ge=0.0, le=1.0)


class QualityResult(BaseModel):
    score: int = Field(..., ge=0, le=100)
    checklist: Dict[str, bool]


class AnalyzeResponse(BaseModel):
    timestamp: datetime
    chat_id: str
    canal: str
    texto_conversa: str

    categoria: str
    categoria_score: float = Field(..., ge=0.0, le=1.0)
    sentimento_inicial: SentimentResult
    sentimento_final: SentimentResult
    qualidade_score: int = Field(..., ge=0, le=100)

    resumo: str
    insights: str
    status_erro: str = ""

    # Compatibilidade com UI atual da extensao
    reason: Dict[str, object]
    sentiment: Dict[str, object]
    quality: QualityResult
    trends: Dict[str, int]
    insights_list: List[str]


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    detail: Optional[str] = None
