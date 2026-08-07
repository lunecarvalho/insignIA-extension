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

        has_greeting = any(token in lower for token in ["ola", "olá", "bom dia", "boa tarde", "boa noite", "oi"])
        has_complaint = any(token in lower for token in ["reclama", "problema", "erro", "falha", "bug", "nao funciona", "não funciona", "parou de funcionar", "não imprime", "não está imprimindo", "não está funcionando", "está travado", "mensagem de erro", "demora"])
        empathy_terms = ["sinto muito", "desculpe", "peço desculpas", "peco desculpas", "entendo", "compreendo", "vou te ajudar", "estou aqui para te auxiliar", "vamos resolver", "vou te auxiliar da melhor forma possível", "estamos à disposição para te ajudar", "estamos a disposicao para te ajudar", "vou te auxiliar"]
        has_empathy = any(token in lower for token in empathy_terms) if has_complaint else False
        has_resolution = any(token in lower for token in ["consegui", "funcionou", "deu certo", "resolvido", "resolveu", "solucionado", "corrigido", "está funcionando agora", "agora funciona", "funcionando agora", "obrigado pela ajuda", "agradeço pela ajuda", "agradeco pela ajuda", "obrigado por ajudar", "agradeço por ajudar", "agradeco por ajudar"])
        has_confirmation = any(token in lower for token in ["obrigado", "agradeço", "agradeco", "gratidão", "grato", "tudo certo", "perfeito", "obrigado pela ajuda", "agradeço pela ajuda", "agradeco pela ajuda", "obrigado por ajudar", "agradeço por ajudar", "agradeco por ajudar"]) or has_resolution
        has_follow_up = any(token in lower for token in ["algo mais", "posso ajudar em algo mais", "mais alguma coisa", "precisa de mais ajuda", "posso ajudar"])
        has_cordiality = any(token in lower for token in ["obrigado", "agradeço", "agradeco", "por favor", "tudo bem", "bom", "certo", "gentileza", "posso ajudar", "algo mais"])
        final_positive_or_improved = (
            sentiment_final == "Positivo"
            or Analyzer._sentiment_to_points(sentiment_final) > Analyzer._sentiment_to_points(sentiment_initial)
        )

        checklist = {
            "saudacao": has_greeting,
            "empatia_quando_reclamacao": has_empathy,
            "resolucao": has_resolution,
            "confirmacao_resolucao": has_confirmation,
            "pergunta_se_ajuda_em_algo_mais": has_follow_up,
            "cordialidade": has_cordiality,
            "sentimento_final_positivo_ou_melhora": final_positive_or_improved,
        }

        score = 0
        if has_greeting:
            score += 10
        if has_empathy:
            score += 15
        if has_resolution:
            score += 35
        if has_confirmation:
            score += 15
        if has_follow_up:
            score += 10
        if has_cordiality:
            score += 10
        if final_positive_or_improved:
            score += 5

        score = max(0, min(100, round(score)))
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

        printer_terms = [
            "impressora", "impress", "scanner", "papel", "fila", "fila de impressão",
            "teste da impressora", "parou de imprimir", "não está imprimindo", "nao esta imprimindo",
            "impressão", "impressao", "teste de impressão", "teste de impressao"
        ]
        login_terms = [
            "login", "senha", "acesso", "entrar", "cadastro", "id e senha", "remote",
            "acesso remoto", "não consigo acessar", "nao consigo acessar", "não consigo entrar",
            "nao consigo entrar", "recuperar senha"
        ]
        payment_terms = [
            "pagamento", "cobran", "boleto", "fatura", "cartao", "cartão",
            "pagamento de boleto", "pagamento de fatura", "pagamento no cartão",
            "pagamento no cartao", "não consigo realizar meu pagamento", "nao consigo realizar meu pagamento"
        ]
        cancellation_terms = [
            "cancel", "reembolso", "estorno", "quero cancelar", "cancelamento",
            "encerrar contrato"
        ]
        menu_terms = [
            "cardapio", "cardápio", "pedido", "menu", "produto", "item", "preço",
            "preco", "cadastrar um item", "alterar o preço", "alterar o preco",
            "remover produto"
        ]
        system_terms = ["erro", "sistema", "bug", "falha", "funcionando"]

        if any(token in lower for token in printer_terms):
            return "Impressora"
        if any(token in lower for token in login_terms) and not any(token in lower for token in printer_terms):
            return "Login"
        if any(token in lower for token in payment_terms):
            return "Financeiro"
        if any(token in lower for token in cancellation_terms):
            return "Cancelamento"
        if any(token in lower for token in menu_terms):
            return "Cardapio"
        if any(token in lower for token in system_terms):
            return "Sistema"
        return "Outro"

    @staticmethod
    def _infer_fallback_sentiment(text: str) -> Tuple[str, float]:
        lower = text.lower()
        negative_terms = [
            "erro", "falha", "bug", "não funciona", "nao funciona", "parou de funcionar",
            "não imprime", "não está imprimindo", "não está funcionando", "está travado",
            "problema", "demora", "mensagem de erro", "reclama", "frustr", "insatisfe"
        ]
        positive_terms = [
            "consegui", "funcionou", "deu certo", "resolvido", "resolveu", "solucionado",
            "corrigido", "obrigado", "agradeço", "agradeco", "gratidão", "grato",
            "está funcionando agora", "agora funciona", "funcionando agora", "ok", "perfeito", "bom"
        ]

        positive_hits = [term for term in positive_terms if term in lower]
        negative_hits = [term for term in negative_terms if term in lower]

        if positive_hits and not negative_hits:
            return "Positivo", 0.85

        if negative_hits and not positive_hits:
            return "Negativo", 0.85

        if positive_hits and negative_hits:
            if any(term in lower for term in ["obrigado", "agradeço", "agradeco", "gratidão", "grato", "consegui", "funcionou", "deu certo", "resolvido", "resolveu", "solucionado", "corrigido", "está funcionando agora", "agora funciona", "funcionando agora"]):
                return "Positivo", 0.75
            return "Negativo", 0.75

        return "Neutro", 0.5

    @staticmethod
    def _summary_fallback(categoria: str, sentimento_inicial: str, sentimento_final: str, text: str) -> str:
        lower = text.lower()

        if categoria == "Login":
            return (
                f"Atendimento de {categoria} com foco em recuperação de acesso e orientação para login. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        if categoria == "Impressora":
            return (
                f"Atendimento de {categoria} com relato de problema de impressão e tentativa de solução. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        if categoria == "Financeiro":
            return (
                f"Atendimento de {categoria} com foco em cobrança, pagamento ou pendência financeira. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        if categoria == "Cancelamento":
            return (
                f"Atendimento de {categoria} com solicitação de cancelamento, reembolso ou encerramento. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        if categoria == "Cardapio":
            return (
                f"Atendimento de {categoria} com solicitação relacionada a item, produto ou alteração de menu. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        if categoria == "Sistema":
            return (
                f"Atendimento de {categoria} com relato de falha ou problema técnico. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        if "login" in lower or "senha" in lower or "acesso" in lower:
            return (
                f"Atendimento de {categoria} com foco em recuperação de acesso e orientação para login. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        if "problema" in lower or "erro" in lower or "impress" in lower or "fila" in lower:
            return (
                f"Atendimento de {categoria} com relato de problema e tentativa de solução. "
                f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}."
            )
        return (
            f"Atendimento classificado como {categoria}. "
            f"Sentimento inicial {sentimento_inicial} e final {sentimento_final}. "
            "Houve tratativa com foco em orientação e fechamento."
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
            fallback_text = initial_chunk.strip()
            if len(fallback_text.split()) <= 2 and len(payload.mensagens) > 1:
                fallback_text = " ".join(msg.strip() for msg in payload.mensagens[:2] if msg and msg.strip())
            if not fallback_text:
                fallback_text = masked_text
            initial_label, initial_score = self._infer_fallback_sentiment(fallback_text)
            status_errors.append("fallback_sentimento_inicial")

        try:
            final_label, final_score = self.hf_client.sentiment(final_chunk, self.sentiment_model)
        except HFClientError as exc:
            logger.warning(f"Fallback sentimento final: {exc}")
            fallback_text = final_chunk.strip()
            if len(fallback_text.split()) <= 2 and len(payload.mensagens) > 1:
                fallback_text = " ".join(msg.strip() for msg in payload.mensagens[-2:] if msg and msg.strip())
            if not fallback_text:
                fallback_text = masked_text
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
