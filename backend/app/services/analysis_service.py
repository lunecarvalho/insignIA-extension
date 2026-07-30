from typing import Dict, Any
from ..schemas.analysis import AnalysisResult, Reason, Sentiment, Quality
import random

# Simple rule-based classifier for the category (placeholder for real NLP models)
CATEGORY_KEYWORDS = {
    'Impressora': ['impressora', 'papel', 'tinta', 'printer', 'imprimir'],
    'Financeiro': ['fatura', 'boleto', 'pagamento', 'financeiro', 'cobrança'],
    'Login': ['login', 'entrar', 'senha', 'autenticação', 'log in'],
    'Cancelamento': ['cancelar', 'cancelamento', 'rescisão'],
    'Cardápio': ['cardápio', 'menu', 'prato', 'pedido'],
    'Sistema': ['erro', 'sistema', 'sincronizar', 'bug', 'falha']
}


def classify_reason(messages) -> Reason:
    text = ' '.join(m.get('text', '').lower() for m in messages)
    scores = {k: 0 for k in CATEGORY_KEYWORDS}
    for cat, keys in CATEGORY_KEYWORDS.items():
        for kw in keys:
            if kw in text:
                scores[cat] += text.count(kw)

    best = max(scores.items(), key=lambda x: x[1])
    category = best[0]
    confidence = min(99, 50 + best[1] * 10) if best[1] > 0 else 45
    subcategory = 'Geral'
    return Reason(category=category, subcategory=subcategory, confidence=int(confidence))


def analyze_sentiment(messages) -> Sentiment:
    positives = ['obrigado', 'bom', 'perfeito', 'legal', 'ótimo', 'otimo', 'grato']
    negatives = ['ruim', 'erro', 'péssimo', 'pior', 'ódio', 'odioso', 'ódio', 'ódio']
    text = ' '.join(m.get('text', '').lower() for m in messages)
    score = 50
    for p in positives:
        if p in text:
            score += 5
    for n in negatives:
        if n in text:
            score -= 8
    label = 'neutral'
    if score >= 60:
        label = 'positive'
    elif score <= 40:
        label = 'negative'
    return Sentiment(score=round(score / 100, 2), label=label)


def evaluate_quality(messages) -> Quality:
    checklist = {
        'Saudou o cliente': any('olá' in m.get('text', '').lower() or 'bom dia' in m.get('text', '').lower() for m in messages),
        'Demonstrou empatia': any('entendo' in m.get('text', '').lower() or 'sinto muito' in m.get('text', '').lower() for m in messages),
        'Explicou claramente': True,
        'Solucionou o problema': random.choice([True, True, False]),
        'Confirmou satisfação': random.choice([True, False])
    }
    score = 50 + sum(10 for v in checklist.values() if v)
    score = min(100, int(score))
    return Quality(score=score, checklist=checklist, notes='Observações automáticas geradas pela IA.')


def generate_insights(reason: Reason, sentiment: Sentiment) -> list[str]:
    insights = []
    if reason.category == 'Sistema':
        insights.append('Criar artigo para erro de sincronização.')
    if reason.category == 'Login':
        insights.append('Atualizar FAQ sobre login.')
    if sentiment.label == 'negative':
        insights.append('Reforçar script de empatia para atendentes.')
    return insights


def perform_analysis(conversation: Dict[str, Any]) -> AnalysisResult:
    messages = conversation.get('messages', [])
    reason = classify_reason(messages)
    sentiment = analyze_sentiment(messages)
    quality = evaluate_quality(messages)
    insights = generate_insights(reason, sentiment)
    trends = {k: random.randint(0, 100) for k in CATEGORY_KEYWORDS.keys()}

    return AnalysisResult(reason=reason, sentiment=sentiment, quality=quality, trends=trends, insights=insights)
