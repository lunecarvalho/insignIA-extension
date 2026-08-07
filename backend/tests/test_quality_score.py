from app.services.analyzer import Analyzer


def test_quality_score_heuristic_full_points():
    text = (
        "Ola, sinto muito pelo problema. "
        "Vou orientar o passo a passo da solucao. "
        "Seu caso foi resolvido, posso ajudar em algo mais?"
    )
    score, checklist = Analyzer.calculate_quality_score(text, "Negativo", "Positivo")

    assert score == 100
    assert all(checklist.values())


def test_quality_score_heuristic_low_points():
    text = "cliente relata erro sem resposta objetiva"
    score, checklist = Analyzer.calculate_quality_score(text, "Negativo", "Negativo")

    assert score <= 20
    assert checklist["sentimento_final_positivo_ou_melhora"] is False


def test_resolution_has_more_weight_than_greeting():
    greeting_score, _ = Analyzer.calculate_quality_score("Olá, bom dia!", "Neutro", "Neutro")
    resolution_score, _ = Analyzer.calculate_quality_score("Resolvido.", "Neutro", "Neutro")

    assert resolution_score > greeting_score


def test_gratitude_for_help_marks_resolution():
    _, checklist = Analyzer.calculate_quality_score("Obrigado pela ajuda.", "Negativo", "Positivo")

    assert checklist["resolucao"] is True
    assert checklist["confirmacao_resolucao"] is True


def test_empathy_phrases_mark_complaint_response():
    _, checklist = Analyzer.calculate_quality_score("Tenho um problema. Vou te ajudar.", "Negativo", "Negativo")

    assert checklist["empatia_quando_reclamacao"] is True
