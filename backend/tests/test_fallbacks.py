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
    assert "impressão" in result.resumo.lower() or "impressora" in result.resumo.lower()
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


def test_fallback_prioritizes_printer_keywords_over_login_keywords():
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
        chat_id="chat-5",
        canal="whatsapp",
        mensagens=[
            "Olá, minha impressora parou de imprimir.",
            "Boa tarde! Vou te ajudar, me informa o ID e senha do seu acesso remoto, por gentileza?",
            "Claro, segue ID: XXXX Senha: hfdjjhh",
            "Obrigada! Vou acessar, só um momento.",
            "Verifica se o teste da impressora saiu agora, por favor?",
            "Sim, funcionou. Obrigado pela ajuda",
            "Imagina! Algo mais que eu possa te ajudar?",
            "Somente, obrigado",
        ],
    )

    result = analyzer.analyze(payload)

    assert result.categoria == "Impressora"


def test_fallback_classifies_menu_change_request_as_cardapio():
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
        chat_id="chat-6",
        canal="whatsapp",
        mensagens=[
            "Olá, preciso cadastrar um item no cardápio.",
            "Quero alterar o preço de um produto.",
            "Obrigada, consegui fazer.",
        ],
    )

    result = analyzer.analyze(payload)

    assert result.categoria == "Cardapio"


def test_fallback_final_sentiment_uses_last_short_message():
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
        chat_id="chat-4",
        canal="whatsapp",
        mensagens=[
            "Olá, estou com problema no login.",
            "Preciso recuperar minha senha.",
            "Obrigado!",
        ],
    )

    result = analyzer.analyze(payload)

    assert result.sentimento_final.label == "Positivo"
