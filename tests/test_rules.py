import pytest

from app.rules import (
    is_emergency,
    is_low_confidence,
    load_emergency_keywords,
    matches_emergency_keyword,
    normalize_text,
)


@pytest.mark.parametrize(
    "message",
    [
        "tem um fio caido na minha rua",
        "FIO CAÍDO NA CALÇADA!!!",
        "o poste caiu em cima do carro",
        "poste caido aqui na frente",
        "ta saindo faisca do transformador",
        "esta faiscando muito",
        "a casa do vizinho esta pegando fogo",
        "meu filho deu choque na tomada do poste",
        "levei choque ao encostar no portao",
        "fio   caido\nna esquina",
        "o transformador explodiu agora",
    ],
)
def test_emergency_keywords_are_detected(message: str) -> None:
    assert matches_emergency_keyword(message)


@pytest.mark.parametrize(
    "message",
    [
        "estou sem luz desde ontem a noite",
        "minha conta veio muito alta",
        "quero religar minha energia",
        "o choque de preco da conta me assustou",
        "ele caiu da escada e nao tem luz",
        "",
    ],
)
def test_non_emergency_messages_do_not_match(message: str) -> None:
    assert not matches_emergency_keyword(message)


def test_keyword_does_not_match_inside_other_words() -> None:
    assert not matches_emergency_keyword("o sofio caidonado")


def test_keywords_override_llm_saying_no_emergency() -> None:
    assert is_emergency("fio caido na rua", llm_flagged_emergency=False)


def test_llm_emergency_counts_without_keyword() -> None:
    assert is_emergency("tem um negocio estranho no poste", llm_flagged_emergency=True)


def test_no_emergency_when_neither_signals() -> None:
    assert not is_emergency("estou sem luz", llm_flagged_emergency=False)


def test_confidence_below_threshold_goes_to_human() -> None:
    assert is_low_confidence(0.69, threshold=0.7)


def test_confidence_at_threshold_is_accepted() -> None:
    assert not is_low_confidence(0.7, threshold=0.7)


def test_threshold_comes_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.9")
    assert is_low_confidence(0.8)
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.5")
    assert not is_low_confidence(0.8)


def test_normalize_text_strips_accents_and_punctuation() -> None:
    assert normalize_text("Fio CAÍDO!!") == " fio caido "


def test_every_configured_keyword_matches_itself() -> None:
    for keyword in load_emergency_keywords():
        assert matches_emergency_keyword(keyword)
