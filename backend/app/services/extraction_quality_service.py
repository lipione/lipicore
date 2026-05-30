def build_extraction_quality(
    *,
    extraction_confidence: float | None,
    ocr_confidence: float | None,
    table_confidence: float | None,
    text: str | None,
) -> dict:
    flags: list[str] = []
    if not (text or "").strip():
        flags.append("empty_text")
    if extraction_confidence is not None and extraction_confidence < 0.75:
        flags.append("low_extraction_confidence")
    if ocr_confidence is not None and ocr_confidence < 0.70:
        flags.append("low_ocr_confidence")
    if table_confidence is not None and table_confidence < 0.75:
        flags.append("low_table_confidence")

    if (
        "empty_text" in flags
        or "low_ocr_confidence" in flags
        or "low_table_confidence" in flags
    ):
        quality_bucket = "review_required"
    elif flags:
        quality_bucket = "caution"
    else:
        quality_bucket = "reliable"

    return {"quality_bucket": quality_bucket, "flags": flags}
