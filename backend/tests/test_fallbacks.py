from app.models import AnalyzeRequest
from app.services.analyzer import Analyzer
from app.services.hf_client import HFClientError


class FailingHFClient:
    def sentiment(self, text, model):
        raise HFClientError("sentiment down")

    def zero_shot(self, text, labels, model):
        raise HFClientError("zero-shot down")

    def summarize(self, text, model):
        raise HFClientError("summary down")


class FakeSheetsClient:
    def __init__(self):
        self.last_row = None

    def append_analysis_row(self, row):
        self.last_row = row


def test_fallback_when_hf_fails():
    sheets = FakeSheetsClient()
    analyzer = Analyzer(
        hf_client=FailingHFClient(),
        sheets_client=sheets,
        sentiment_model="sent",
        zero_shot_model="zs",
        summary_model="sum",
        max_text_chars=12000,
    )

    payload = AnalyzeRequest(
        chat_id="chat-1",
        canal="whatsapp",
        mensagens=["Ola", "cliente reclama de erro", "vamos resolver agora"],
    )

    result = analyzer.analyze(payload)

    assert result.categoria == "Sistema"
    assert result.sentimento_inicial.label == "Negativo"


def test_fallback_classifies_printer_issue_as_impressora():
    sheets = FakeSheetsClient()
    analyzer = Analyzer(
        hf_client=FailingHFClient(),
        sheets_client=sheets,
        sentiment_model="sent",
        zero_shot_model="zs",
        summary_model="sum",
        max_text_chars=12000,
    )

    payload = AnalyzeRequest(
        chat_id="chat-3",
        canal="whatsapp",
        mensagens=[
            "Olá, a impressora não está imprimindo.",
            "Preciso de ajuda com a fila de impressão.",
            "Obrigado, agora funcionou.",
        ],
    )

    result = analyzer.analyze(payload)

    assert result.categoria == "Impressora"
    assert result.sentimento_final.label == "Positivo"
    assert "fallback_categoria" in result.status_erro
    assert "fallback_resumo" in result.status_erro
    assert sheets.last_row is not None


def test_fallback_uses_text_keywords_when_models_fail():
    sheets = FakeSheetsClient()
    analyzer = Analyzer(
        hf_client=FailingHFClient(),
        sheets_client=sheets,
        sentiment_model="sent",
        zero_shot_model="zs",
        summary_model="sum",
        max_text_chars=12000,
    )

    payload = AnalyzeRequest(
        chat_id="chat-2",
        canal="whatsapp",
        mensagens=[
            "Olá, estou com problema no login.",
            "Preciso recuperar minha senha.",
            "Consegui acessar, obrigado!",
        ],
    )

    result = analyzer.analyze(payload)

    assert result.categoria == "Login"
    assert result.sentimento_inicial.label == "Negativo"
    assert result.sentimento_final.label == "Positivo"
    assert "login" in result.resumo.lower()
    assert "fallback_resumo" in result.status_erro
