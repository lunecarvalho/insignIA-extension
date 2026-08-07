import re


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9?\d{4})-?\d{4}\b")
CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b")


def mask_pii(text: str) -> str:
    """Mascara dados pessoais para reduzir risco de vazamento para APIs externas."""
    masked = EMAIL_RE.sub("[EMAIL]", text)
    masked = PHONE_RE.sub("[TELEFONE]", masked)
    masked = CPF_RE.sub("[CPF]", masked)
    return masked
