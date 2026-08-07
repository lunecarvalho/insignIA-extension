from datetime import datetime, timezone
from typing import Dict, List, Tuple
from ..config import Settings
from ..core.logging import logger
from ..models import AnalyzeRequest, AnalyzeResponse, CategoryResult, QualityResult, SentimentResult
from .hf_client import HFClientError, HuggingFaceClient
from .pii_mask import mask_pii
from .sheets_client import GoogleSheetsClient, SheetsWriteError


ZERO_SHOT_LABELS = [
    "Impressora",
    "Financeiro",
    "Login",
    "Cancelamento",
    "Cardapio",
    "Sistema",
    "Outro",
]


class AnalyzerError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_code: str = "ANALYZER_ERROR", detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail


class Analyzer:
    def __init__(
        self,
        hf_client: HuggingFaceClient,
        sheets_client: GoogleSheetsClient,
        sentiment_model: str,
        zero_shot_model: str,
        summary_model: str,
        max_text_chars: int = 12000,
    ):
        self.hf_client = hf_client
        self.sheets_client = sheets_client
        self.sentiment_model = sentiment_model
        self.zero_shot_model = zero_shot_model
        self.summary_model = summary_model
        self.max_text_chars = max_text_chars

    @staticmethod
    def _join_messages(messages: List[str]) -> str:
        return "\n".join(item.strip() for item in messages if item and item.strip())

    @staticmethod
    def _split_for_sentiment(messages: List[str]) -> Tuple[str, str]:
        n = len(messages)
        chunk = max(1, int(round(n * 0.2)))
        start = " ".join(messages[:chunk])
        end = " ".join(messages[-chunk:])
        return start, end

    @staticmethod
    def _normalize_category(label: str) -> str:
        if label.lower() == "cardapio":
            return "Cardapio"
        normalized = label.strip().title()
        return normalized if normalized in ZERO_SHOT_LABELS else "Outro"

    @staticmethod
    def _sentiment_to_points(label: str) -> int:
        if label == "Positivo":
            return 2
        if label == "Neutro":
            return 1
        return 0

    @staticmethod
    def calculate_quality_score(text: str, sentiment_initial: str, sentiment_final: str) -> Tuple[int, Dict[str, bool]]:
        lower = text.lower()

        has_greeting = any(token in lower for token in ["ola", "olá", "bom dia", "boa tarde", "boa noite"])
        has_complaint = any(token in lower for token in ["reclama", "problema", "erro", "ruim", "nao funciona", "não funciona"])
        has_empathy = any(token in lower for token in ["sinto muito", "desculpe", "peço desculpas", "peco desculpas", "entendo"]) if has_complaint else False
        has_solution = any(token in lower for token in ["orient", "solucao", "solução", "passo", "ajuste", "corrigi", "corrigimos"])
        has_closure = any(token in lower for token in ["resolvido", "encerr", "conclui", "algo mais", "posso ajudar em algo mais"])
        final_positive_or_improved = (
            sentiment_final == "Positivo"
            or Analyzer._sentiment_to_points(sentiment_final) > Analyzer._sentiment_to_points(sentiment_initial)
        )

        checklist = {
            "saudacao": has_greeting,
            "empatia_quando_reclamacao": has_empathy,
            "orientacao_solucao": has_solution,
            "confirmacao_encerramento": has_closure,
            "sentimento_final_positivo_ou_melhora": final_positive_or_improved,
        }

        score = sum(20 for ok in checklist.values() if ok)
        score = max(0, min(100, score))
        return score, checklist

    @staticmethod
    def build_insights(categoria: str, sentimento_final: str, qualidade_score: int, status_erro: str) -> str:
        if status_erro:
            return "Analise concluida com fallback parcial; revisar disponibilidade dos modelos e integrações."
        if qualidade_score >= 80 and sentimento_final == "Positivo":
            return f"Atendimento consistente para {categoria}; manter roteiro atual e replicar boas praticas."
        if qualidade_score < 60:
            return f"Reforcar empatia e encerramento no fluxo de {categoria}; ha oportunidades claras de melhoria."
        return f"Atendimento estavel em {categoria}; monitorar para elevar conversao para sentimento positivo no fechamento."

    @staticmethod
    def _infer_fallback_category(text: str) -> str:
        lower = text.lower()
        if any(token in lower for token in ["login", "senha", "acesso", "entrar", "cadastro"]):
            return "Login"
        if any(token in lower for token in ["pagamento", "cobran", "boleto", "fatura", "cartao"]):
            return "Financeiro"
        if any(token in lower for token in ["impress", "scanner", "papel", "fila"]):
            return "Impressora"
        if any(token in lower for token in ["cancel", "reembolso", "estorno"]):
            return "Cancelamento"
        if any(token in lower for token in ["cardapio", "pedido", "menu"]):
            return "Cardapio"
        if any(token in lower for token in ["erro", "sistema", "bug", "falha", "funcionando"]):
            return "Sistema"
        return "Outro"

    @staticmethod
    def _infer_fallback_sentiment(text: str) -> Tuple[str, float]:
        lower = text.lower()
        negative_terms = ["problema", "erro", "reclama", "nao", "não", "frustr", "insatisfe", "demora", "falha", "ruim", "não funciona", "nao funciona"]
        positive_terms = ["consegui", "funcionou", "obrigado", "resolveu", "ok", "perfeito", "bom", "solucionado", "corrigido"]
        if any(term in lower for term in positive_terms) and not any(term in lower for term in negative_terms):
            return "Positivo", 0.8
        if any(term in lower for term in negative_terms):
            return "Negativo", 0.8
        return "Neutro", 0.5

    @staticmethod
    def _summary_fallback(categoria: str, sentimento_inicial: str, sentimento_final: str, text: str) -> str:
        lower = text.lower()
        if "login" in lower or "senha" in lower or "acesso" in lower:
            return (
                f"Atendimento de {categoria} com foco em recuperação de acesso e orientacao para login. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        if "problema" in lower or "erro" in lower:
            return (
                f"Atendimento de {categoria} com relato de problema e tentativa de solução. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        return (
            f"Atendimento classificado como {categoria}. "
            f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}. "
            "Houve tratativa com foco em orientacao e fechamento."
        )

    def analyze(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        text = self._join_messages(payload.mensagens)
        masked_text = mask_pii(text)[: self.max_text_chars]
        initial_chunk, final_chunk = self._split_for_sentiment(payload.mensagens)
        initial_chunk = mask_pii(initial_chunk)[: self.max_text_chars]
        final_chunk = mask_pii(final_chunk)[: self.max_text_chars]

        status_errors: List[str] = []

        try:
            initial_label, initial_score = self.hf_client.sentiment(initial_chunk, self.sentiment_model)
        except HFClientError as exc:
            logger.warning(f"Fallback sentimento inicial: {exc}")
            fallback_text = masked_text if len(initial_chunk.split()) <= 2 else initial_chunk
            initial_label, initial_score = self._infer_fallback_sentiment(fallback_text)
            status_errors.append("fallback_sentimento_inicial")

        try:
            final_label, final_score = self.hf_client.sentiment(final_chunk, self.sentiment_model)
        except HFClientError as exc:
            logger.warning(f"Fallback sentimento final: {exc}")
            fallback_text = masked_text if len(final_chunk.split()) <= 2 else final_chunk
            final_label, final_score = self._infer_fallback_sentiment(fallback_text)
            status_errors.append("fallback_sentimento_final")

        try:
            category_label, category_score = self.hf_client.zero_shot(masked_text, ZERO_SHOT_LABELS, self.zero_shot_model)
            category_label = self._normalize_category(category_label)
        except HFClientError as exc:
            logger.warning(f"Fallback categoria: {exc}")
            category_label, category_score = self._infer_fallback_category(masked_text), 0.0
            status_errors.append("fallback_categoria")

        try:
            summary = self.hf_client.summarize(masked_text, self.summary_model)
        except HFClientError as exc:
            logger.warning(f"Fallback resumo: {exc}")
            summary = self._summary_fallback(category_label, initial_label, final_label, masked_text)
            status_errors.append("fallback_resumo")

        quality_score, checklist = self.calculate_quality_score(masked_text, initial_label, final_label)
        status_erro = ";".join(status_errors)
        insights = self.build_insights(category_label, final_label, quality_score, status_erro)
        timestamp = datetime.now(timezone.utc)

        row = {
            "timestamp": timestamp.isoformat(),
            "chat_id": payload.chat_id,
            "canal": payload.canal,
            "texto_conversa": masked_text,
            "categoria": category_label,
            "categoria_score": category_score,
            "sentimento_inicial": initial_label,
            "sentimento_final": final_label,
            "qualidade_score": quality_score,
            "resumo": summary,
            "insights": insights,
            "status_erro": status_erro,
        }

        try:
            self.sheets_client.append_analysis_row(row)
        except SheetsWriteError as exc:
            logger.exception("Erro tecnico ao gravar no Google Sheets")
            raise AnalyzerError(
                message="Nao foi possivel salvar o resultado na planilha. Tente novamente em instantes.",
                status_code=503,
                error_code="SHEETS_WRITE_ERROR",
                detail=str(exc),
            )

        response = AnalyzeResponse(
            timestamp=timestamp,
            chat_id=payload.chat_id,
            canal=payload.canal,
            texto_conversa=masked_text,
            categoria=category_label,
            categoria_score=category_score,
            sentimento_inicial=SentimentResult(label=initial_label, score=initial_score),
            sentimento_final=SentimentResult(label=final_label, score=final_score),
            qualidade_score=quality_score,
            resumo=summary,
            insights=insights,
            status_erro=status_erro,
            reason={
                "category": category_label,
                "subcategory": "Geral",
                "confidence": int(round(category_score * 100)),
            },
            sentiment={
                "label": final_label.lower(),
                "score": round(final_score, 3),
            },
            quality=QualityResult(score=quality_score, checklist=checklist),
            trends={},
            insights_list=[insights],
        )
        return response


def build_analyzer_from_settings(settings: Settings) -> Analyzer:
    try:
        hf_client = HuggingFaceClient(
            api_token=settings.HF_API_TOKEN,
            timeout_seconds=settings.HF_TIMEOUT_SECONDS,
            max_retries=settings.HF_MAX_RETRIES,
        )
        sheets_client = GoogleSheetsClient(
            spreadsheet_id=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
            service_account_json=settings.GOOGLE_SERVICE_ACCOUNT_JSON,
            tab_name=settings.GOOGLE_SHEETS_TAB_NAME,
        )
    except Exception as exc:
        raise AnalyzerError(
            message="Configuracao do backend incompleta para analise.",
            status_code=500,
            error_code="SETTINGS_ERROR",
            detail=str(exc),
        )

    return Analyzer(
        hf_client=hf_client,
        sheets_client=sheets_client,
        sentiment_model=settings.HF_SENTIMENT_MODEL,
        zero_shot_model=settings.HF_ZERO_SHOT_MODEL,
        summary_model=settings.HF_SUMMARY_MODEL,
        max_text_chars=settings.MAX_TEXT_CHARS,
    )
