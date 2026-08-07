from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app import main as main_module


client = TestClient(main_module.app)


class FakeAnalyzer:
    def analyze(self, payload):
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "chat_id": payload.chat_id,
            "canal": payload.canal,
            "texto_conversa": "texto",
            "categoria": "Outro",
            "categoria_score": 0.0,
            "sentimento_inicial": {"label": "Neutro", "score": 0.5},
            "sentimento_final": {"label": "Neutro", "score": 0.5},
            "qualidade_score": 20,
            "resumo": "Resumo curto.",
            "insights": "Insight curto.",
            "status_erro": "",
            "reason": {"category": "Outro", "subcategory": "Geral", "confidence": 0},
            "sentiment": {"label": "neutral", "score": 0.5},
            "quality": {"score": 20, "checklist": {"saudacao": True}},
            "trends": {},
            "insights_list": ["Insight curto."],
        }


def test_analyze_payload_validation_error():
    response = client.post("/analyze", json={"chat_id": "abc", "canal": "whatsapp", "mensagens": []})
    assert response.status_code == 422


def test_analyze_payload_success(monkeypatch):
    monkeypatch.setattr(main_module, "get_analyzer", lambda: FakeAnalyzer())
    response = client.post(
        "/analyze",
        json={
            "chat_id": "chat-1",
            "canal": "whatsapp",
            "mensagens": ["Ola", "Tudo certo"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["chat_id"] == "chat-1"
    assert body["canal"] == "whatsapp"
