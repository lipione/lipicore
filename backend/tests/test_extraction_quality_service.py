from app.services.extraction_quality_service import build_extraction_quality


def test_quality_marks_low_ocr_confidence_for_review():
    result = build_extraction_quality(
        extraction_confidence=0.82,
        ocr_confidence=0.41,
        table_confidence=None,
        text="Visible but noisy OCR text",
    )

    assert result["quality_bucket"] == "review_required"
    assert "low_ocr_confidence" in result["flags"]


def test_quality_marks_table_review_when_table_confidence_is_low():
    result = build_extraction_quality(
        extraction_confidence=0.95,
        ocr_confidence=None,
        table_confidence=0.52,
        text="Row 1: Customer | Limit",
    )

    assert result["quality_bucket"] == "review_required"
    assert "low_table_confidence" in result["flags"]


def test_quality_marks_clean_direct_text_as_reliable():
    result = build_extraction_quality(
        extraction_confidence=0.97,
        ocr_confidence=None,
        table_confidence=None,
        text="Section 1 Staff must verify identity.",
    )

    assert result["quality_bucket"] == "reliable"
    assert result["flags"] == []
