from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.conversation import ConversationCreate
from ..schemas.analysis import AnalysisResult
from ..db.session import get_db
from ..services.analysis_service import perform_analysis
from ..services.history_service import HistoryService
from ..core.logging import logger

router = APIRouter()


@router.post('/analisar', response_model=AnalysisResult)
def analisar(conversation: ConversationCreate, db: Session = Depends(get_db)):
    """Endpoint principal: recebe uma conversa, processa com a 'IA' e retorna análise."""
    try:
        result = perform_analysis(conversation.dict())
        # salvar no histórico de forma síncrona
        history = HistoryService(db)
        history.save_conversation_and_analysis(conversation.dict(), result)
        return result
    except Exception as e:
        logger.exception('Erro na rota /analisar')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/historico')
def post_historico(conversation: ConversationCreate, db: Session = Depends(get_db)):
    """Salvar apenas a conversa (sem análise)."""
    try:
        conv_repo = HistoryService(db)
        saved = conv_repo.save_conversation_and_analysis(conversation.dict(), perform_analysis(conversation.dict()))
        return {'status': 'ok', 'id': saved['conversation'].id}
    except Exception as e:
        logger.exception('Erro em POST /historico')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/historico')
def get_historico(limit: int = 50, db: Session = Depends(get_db)):
    try:
        history = HistoryService(db)
        items = history.list_history(limit)
        return items
    except Exception as e:
        logger.exception('Erro em GET /historico')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/dashboard')
def get_dashboard(db: Session = Depends(get_db)):
    try:
        # Aggregate basic dashboard metrics
        history = HistoryService(db)
        analyses = history.list_history(100)
        total = len(analyses)
        avg_quality = 0
        if total:
            avg_quality = sum([a.quality['score'] for a in analyses]) / total
        return {'total_analyses': total, 'avg_quality': avg_quality}
    except Exception as e:
        logger.exception('Erro em GET /dashboard')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/tendencias')
def get_tendencias(db: Session = Depends(get_db)):
    try:
        history = HistoryService(db)
        trends = history.get_trends()
        return trends
    except Exception as e:
        logger.exception('Erro em GET /tendencias')
        raise HTTPException(status_code=500, detail=str(e))
