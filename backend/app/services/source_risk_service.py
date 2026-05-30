import re
from typing import TypedDict


class SourceRisk(TypedDict):
    risk_level: str
    flags: list[str]


HIGH_RISK_PATTERNS = (
    re.compile(r"\bignore\s+(all\s+)?previous\s+instructions\b", re.IGNORECASE),
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"\breveal\s+(the\s+)?(prompt|instructions|secrets)\b", re.IGNORECASE),
    re.compile(r"\bdeveloper\s+message\b", re.IGNORECASE),
)

MEDIUM_RISK_PATTERNS = (
    re.compile(r"\bdo\s+not\s+cite\b", re.IGNORECASE),
    re.compile(r"\bwithout\s+citation\b", re.IGNORECASE),
    re.compile(r"\banswer\s+from\s+general\s+knowledge\b", re.IGNORECASE),
    re.compile(r"\bdisable\s+(rag|retrieval|guardrails)\b", re.IGNORECASE),
)


def classify_source_risk(text: str | None) -> SourceRisk:
    value = text or ""
    flags: list[str] = []
    for pattern in HIGH_RISK_PATTERNS:
        if pattern.search(value):
            flags.append("prompt_injection_instruction")
            break
    for pattern in MEDIUM_RISK_PATTERNS:
        if pattern.search(value):
            flags.append("citation_suppression")
            break

    if "prompt_injection_instruction" in flags:
        risk_level = "high"
    elif flags:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {"risk_level": risk_level, "flags": flags}
