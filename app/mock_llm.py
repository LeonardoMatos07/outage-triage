from rapidfuzz import fuzz

from app.llm import LlmResponse
from app.neighborhoods import load_neighborhoods
from app.rules import matches_emergency_keyword, normalize_text
from app.schemas import Intent, Scope, TriageResult
from app.settings import MOCK_MODEL_NAME

FUZZY_NEIGHBORHOOD_CUTOFF = 85
MAX_NEIGHBORHOOD_WORDS = 3
SHORT_MESSAGE_WORDS = 4
CLEAR_CONFIDENCE = 0.9
GENERIC_CONFIDENCE = 0.75
VAGUE_CONFIDENCE = 0.4
MAX_SINCE_LENGTH = 40
MOCK_NOTE = "resposta simulada pelo modo mock"

EXTRA_EMERGENCY_TERMS = (
    "fumaca",
    "estalos",
    "cheiro de queimado",
    "eletrizado",
    "preso no fio",
    "fio de alta tensao",
    "cabo de energia se soltou",
)
RECONNECTION_TERMS = (
    "religa",
    "cortaram",
    "cortada",
    "corte",
    "ligacao nova",
    "ligacao de energia",
)
OUTAGE_TERMS = (
    "sem luz",
    "sem energia",
    "faltou",
    "falta de luz",
    "acabou a luz",
    "luz acabou",
    "luz caiu",
    "caiu a luz",
    "caiu a energia",
    "luz foi embora",
    "apagou",
    "piscando",
    "piscou",
)
BILLING_TERMS = (
    "conta",
    "fatura",
    "boleto",
    "cobr",
    "tarifa",
    "debito",
    "juros",
    "segunda via",
    "vencimento",
    "reembolso",
    "kwh",
)
MY_HOME_TERMS = (
    "so aqui em casa",
    "so a minha casa",
    "so minha casa",
    "so na minha casa",
    "so no meu apartamento",
    "minha casa esta sem",
    "so a tomada",
)
WIDER_SCOPE_TERMS = (
    "rua toda",
    "rua inteira",
    "bairro todo",
    "no bairro",
    "vizinhos",
    "predio inteiro",
    "quarteirao",
    "todo mundo",
    "e geral",
    "area",
)


def contains_any(normalized: str, terms: tuple[str, ...]) -> bool:
    return any(normalize_text(term).strip() in normalized for term in terms)


def find_neighborhood(normalized: str) -> str | None:
    names = load_neighborhoods()
    for name in names:
        if normalize_text(name) in normalized:
            return name
    words = normalized.split()
    for size in range(MAX_NEIGHBORHOOD_WORDS, 0, -1):
        for start in range(len(words) - size + 1):
            candidate = " ".join(words[start : start + size])
            for name in names:
                if fuzz.ratio(candidate, normalize_text(name).strip()) >= FUZZY_NEIGHBORHOOD_CUTOFF:
                    return candidate
    return None


def detect_intent(normalized: str, emergency: bool) -> Intent:
    if emergency:
        return Intent.OUTAGE
    if contains_any(normalized, RECONNECTION_TERMS):
        return Intent.RECONNECTION
    if contains_any(normalized, OUTAGE_TERMS):
        return Intent.OUTAGE
    if contains_any(normalized, BILLING_TERMS):
        return Intent.BILLING
    return Intent.OTHER


def detect_scope(normalized: str) -> Scope:
    if contains_any(normalized, MY_HOME_TERMS):
        return Scope.MY_HOME
    if contains_any(normalized, WIDER_SCOPE_TERMS):
        return Scope.STREET_OR_AREA
    return Scope.UNKNOWN


def detect_outage_since(normalized: str) -> str | None:
    marker = " desde "
    if marker not in normalized:
        return None
    return normalized.split(marker, 1)[1].strip()[:MAX_SINCE_LENGTH] or None


def detect_confidence(intent: Intent, normalized: str) -> float:
    if intent is not Intent.OTHER:
        return CLEAR_CONFIDENCE
    if len(normalized.split()) <= SHORT_MESSAGE_WORDS:
        return VAGUE_CONFIDENCE
    return GENERIC_CONFIDENCE


def mock_classify(message: str) -> LlmResponse:
    normalized = normalize_text(message)
    emergency = matches_emergency_keyword(message) or contains_any(
        normalized, EXTRA_EMERGENCY_TERMS
    )
    intent = detect_intent(normalized, emergency)
    result = TriageResult(
        intent=intent,
        is_emergency=emergency,
        neighborhood_raw=find_neighborhood(normalized),
        street_or_reference=None,
        outage_since=detect_outage_since(normalized),
        scope=detect_scope(normalized),
        confidence=detect_confidence(intent, normalized),
        notes=MOCK_NOTE,
    )
    return LlmResponse(
        result=result,
        model=MOCK_MODEL_NAME,
        input_tokens=0,
        output_tokens=0,
        latency_seconds=0.0,
    )
