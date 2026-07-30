from sqlalchemy.orm import Session
from ..repositories.conversation_repo import ConversationRepository
from ..repositories.analysis_repo import AnalysisRepository
from ..schemas.analysis import AnalysisResult


class HistoryService:
    def __init__(self, db: Session):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.analysis_repo = AnalysisRepository(db)

    def save_conversation_and_analysis(self, conv_payload: dict, analysis: AnalysisResult):
        conv = self.conv_repo.create(conv_payload)
        analysis_payload = {
            'conversation_id': conv.id,
            'reason': analysis.reason.dict(),
            'sentiment': analysis.sentiment.dict(),
            'quality': analysis.quality.dict(),
            'trends': analysis.trends,
            'insights': analysis.insights
        }
        a = self.analysis_repo.create(analysis_payload)
        return {'conversation': conv, 'analysis': a}

    def list_history(self, limit: int = 100):
        analyses = self.analysis_repo.list_recent(limit)
        return analyses

    def get_trends(self):
        rows = self.analysis_repo.trends()
        return [{ 'category': r[0], 'count': int(r[1]) } for r in rows]
