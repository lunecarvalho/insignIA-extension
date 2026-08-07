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
