import time
from typing import Dict, List, Tuple
import httpx
from ..core.logging import logger


class HFClientError(Exception):
    pass


class HuggingFaceClient:
    def __init__(self, api_token: str, timeout_seconds: int = 30, max_retries: int = 2):
        if not api_token:
            raise HFClientError("HF_API_TOKEN nao configurado")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.client = httpx.Client(
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
        )

    def _post_with_retries(self, model: str, payload: Dict) -> object:
        url = f"https://api-inference.huggingface.co/models/{model}"
        last_error = None
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                response = self.client.post(url, json=payload)
                latency_ms = round((time.perf_counter() - started) * 1000, 2)
                logger.info(f"HF latency model={model} ms={latency_ms}")

                if response.status_code >= 500:
                    raise HFClientError(f"HF {model} status={response.status_code}")
                if response.status_code == 429:
                    raise HFClientError(f"HF {model} rate limited")
                if response.status_code >= 400:
                    raise HFClientError(f"HF {model} bad request status={response.status_code}")

                return response.json()
            except (httpx.TimeoutException, httpx.TransportError, HFClientError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(0.4 * (attempt + 1))

        raise HFClientError(f"Falha na inferencia do modelo {model}: {last_error}")

    @staticmethod
    def _map_sentiment_label(raw_label: str) -> str:
        label = raw_label.lower()
        if "positive" in label or "pos" in label or label.endswith("2"):
            return "Positivo"
        if "negative" in label or "neg" in label or label.endswith("0"):
            return "Negativo"
        return "Neutro"

    def sentiment(self, text: str, model: str) -> Tuple[str, float]:
        body = {"inputs": text}
        data = self._post_with_retries(model, body)
        if not isinstance(data, list) or not data:
            raise HFClientError("Resposta invalida de sentimento")

        candidates = data[0] if isinstance(data[0], list) else data
        if not isinstance(candidates, list) or not candidates:
            raise HFClientError("Resposta sem candidatos de sentimento")

        best = max(candidates, key=lambda item: float(item.get("score", 0.0)))
        label = self._map_sentiment_label(str(best.get("label", "neutral")))
        score = float(best.get("score", 0.0))
        return label, max(0.0, min(score, 1.0))

    def zero_shot(self, text: str, labels: List[str], model: str) -> Tuple[str, float]:
        body = {
            "inputs": text,
            "parameters": {
                "candidate_labels": labels,
                "multi_label": False,
            },
        }
        data = self._post_with_retries(model, body)
        if not isinstance(data, dict):
            raise HFClientError("Resposta invalida de zero-shot")

        out_labels = data.get("labels") or []
        out_scores = data.get("scores") or []
        if not out_labels or not out_scores:
            raise HFClientError("Resposta zero-shot sem labels/scores")

        best_label = str(out_labels[0])
        best_score = float(out_scores[0])
        return best_label, max(0.0, min(best_score, 1.0))

    def summarize(self, text: str, model: str) -> str:
        body = {
            "inputs": text,
            "parameters": {
                "max_length": 160,
                "min_length": 50,
                "do_sample": False,
            },
        }
        data = self._post_with_retries(model, body)
        if not isinstance(data, list) or not data:
            raise HFClientError("Resposta invalida de resumo")

        first = data[0]
        if not isinstance(first, dict):
            raise HFClientError("Resumo sem objeto de saida")

        summary = str(first.get("summary_text", "")).strip()
        if not summary:
            raise HFClientError("Resumo vazio")
        return summary
