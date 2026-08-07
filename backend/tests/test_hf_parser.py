from app.services.hf_client import HuggingFaceClient


def test_parse_sentiment_response(monkeypatch):
    client = HuggingFaceClient(api_token="token", timeout_seconds=5, max_retries=0)
    monkeypatch.setattr(
        client,
        "_post_with_retries",
        lambda model, payload: [[{"label": "negative", "score": 0.1}, {"label": "positive", "score": 0.8}]],
    )

    label, score = client.sentiment("texto", "sent-model")
    assert label == "Positivo"
    assert score == 0.8


def test_parse_zero_shot_response(monkeypatch):
    client = HuggingFaceClient(api_token="token", timeout_seconds=5, max_retries=0)
    monkeypatch.setattr(
        client,
        "_post_with_retries",
        lambda model, payload: {
            "labels": ["Login", "Financeiro"],
            "scores": [0.77, 0.22],
        },
    )

    label, score = client.zero_shot("texto", ["Login", "Financeiro"], "zero-shot-model")
    assert label == "Login"
    assert score == 0.77


def test_parse_summary_response(monkeypatch):
    client = HuggingFaceClient(api_token="token", timeout_seconds=5, max_retries=0)
    monkeypatch.setattr(
        client,
        "_post_with_retries",
        lambda model, payload: [{"summary_text": "Resumo gerado com sucesso."}],
    )

    summary = client.summarize("texto", "summary-model")
    assert summary == "Resumo gerado com sucesso."
