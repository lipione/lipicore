import re
from typing import Any


LEGAL_DEFINITION_RE = re.compile(
    r"\b("
    r"what\s+is|define|definition|meaning\s+of|under\s+(?:nepali\s+)?law|"
    r"कानुन|ऐन|दफा|परिभाषा|भन्नाले"
    r")\b",
    flags=re.IGNORECASE,
)
LEGAL_DOMAIN_RE = re.compile(
    r"\b("
    r"act|law|laws|legal|offence|offense|fraud|banking\s+offence|banking\s+offense|"
    r"nrb|directive|regulation|clause|section|chapter"
    r")\b|ऐन|कानुन|दफा|नियम|परिपत्र|निर्देशन",
    flags=re.IGNORECASE,
)
SOURCE_BACKED_RE = re.compile(
    r"\b("
    r"according\s+to|as\s+per|approved|policy|policies|source|sources|cite|citation|"
    r"document|documents|circular|circulars|directive|directives|sop|manual|"
    r"rule|rules|regulation|regulations|regulatory|nrb|act|law|laws|"
    r"section|sections|clause|clauses|article|articles|quote|quoted|exact"
    r")\b|नीति|स्रोत|दफा|ऐन|नियम|परिपत्र|निर्देशन",
    flags=re.IGNORECASE,
)
PROCEDURE_RE = re.compile(
    r"\b("
    r"how\s+to|steps?|process|procedure|checklist|requirements?|required\s+documents?|"
    r"what\s+should|what\s+must|workflow|escalat(?:e|ion)"
    r")\b",
    flags=re.IGNORECASE,
)
EXTRACT_TEXT_RE = re.compile(
    r"\b("
    r"ocr|"
    r"extract\s+(?:the\s+)?(?:full\s+|all\s+|raw\s+)?text|"
    r"transcribe|read\s+this|scan(?:ned)?\s+text"
    r")\b|पाठ|लेखिएको",
    flags=re.IGNORECASE,
)


def _normalized(message: str | None) -> str:
    return " ".join((message or "").strip().lower().split())


def _source_required(mode: str, text: str) -> bool:
    return mode in {"approved_knowledge", "analyze_file", "compare"} or bool(SOURCE_BACKED_RE.search(text))


def classify_chat_task(
    *,
    message: str | None,
    mode: str,
    active_document_ids: list[int] | None = None,
    has_image: bool = False,
) -> dict[str, Any]:
    text = _normalized(message)
    active_docs = bool(active_document_ids)
    source_required = _source_required(mode, text)

    if has_image or EXTRACT_TEXT_RE.search(text):
        return {
            "task_type": "ocr_extraction",
            "retrieval_intent": "session_file" if active_docs else "none",
            "answer_style": "extracted_text",
            "model_workflow": "vision_ocr" if has_image else "analyze_file",
        }

    if mode == "translate":
        return {
            "task_type": "translation",
            "retrieval_intent": "none",
            "answer_style": "faithful_translation",
            "model_workflow": "ask_knowledge",
        }

    if mode == "draft":
        return {
            "task_type": "drafting",
            "retrieval_intent": "optional" if active_docs else "none",
            "answer_style": "staff_draft",
            "model_workflow": "ask_knowledge",
        }

    if mode == "compare":
        return {
            "task_type": "comparison",
            "retrieval_intent": "source_required",
            "answer_style": "cited_comparison",
            "model_workflow": "compare",
        }

    if mode == "analyze_file" or active_docs:
        return {
            "task_type": "document_analysis",
            "retrieval_intent": "session_file",
            "answer_style": "file_grounded_answer",
            "model_workflow": "analyze_file",
        }

    if LEGAL_DEFINITION_RE.search(text) and LEGAL_DOMAIN_RE.search(text):
        return {
            "task_type": "legal_definition",
            "retrieval_intent": "source_required",
            "answer_style": "cited_definition",
            "model_workflow": "approved_knowledge",
        }

    if mode == "approved_knowledge" or source_required:
        if PROCEDURE_RE.search(text):
            return {
                "task_type": "procedure_checklist",
                "retrieval_intent": "source_required",
                "answer_style": "cited_steps",
                "model_workflow": "approved_knowledge",
            }
        return {
            "task_type": "policy_lookup",
            "retrieval_intent": "source_required",
            "answer_style": "cited_answer",
            "model_workflow": "approved_knowledge",
        }

    return {
        "task_type": "staff_general",
        "retrieval_intent": "optional",
        "answer_style": "general_staff_guidance",
        "model_workflow": "ask_knowledge",
    }
