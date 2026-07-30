from sqlalchemy.orm import Session
from ..models.analysis import Analysis


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict) -> Analysis:
        a = Analysis(**payload)
        self.db.add(a)
        self.db.commit()
        self.db.refresh(a)
        return a

    def list_recent(self, limit: int = 100):
        return self.db.query(Analysis).order_by(Analysis.created_at.desc()).limit(limit).all()

    def trends(self):
        # Simple trends: count by reason->category
        sql = "SELECT (reason->>'category') as category, count(*) as cnt FROM analyses GROUP BY category ORDER BY cnt desc;"
        return self.db.execute(sql).fetchall()
