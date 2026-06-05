from app.services.policy_citation_metadata import (
    build_citation_metadata,
    citation_is_complete_for_policy,
    extract_clause_number,
    extract_document_heading,
    extract_printed_page_number,
)


def test_extracts_policy_heading_clause_and_printed_page_number():
    text = """
    Credit Policy 2024
    Chapter 5: SME Lending
    Clause 5.1(a) Secured SME DSR Limit
    For secured SME loans, debt service ratio must not exceed 60%.

    Page 38
    """

    assert extract_document_heading(text) == "Chapter 5: SME Lending"
    assert extract_clause_number(text) == "Clause 5.1(a)"
    assert extract_printed_page_number(text) == "38"


def test_build_citation_metadata_marks_complete_policy_citation():
    metadata = build_citation_metadata(
        page={"page_number": 42, "text": "Chapter 5: SME Lending\nClause 5.1(a) DSR limit\nPage 38"},
        chunk_text="Clause 5.1(a) DSR limit for secured SME loans is 60%.",
        document_type="policy",
    )

    assert metadata["pdf_page_number"] == 42
    assert metadata["printed_page_number"] == "38"
    assert metadata["document_heading"] == "Chapter 5: SME Lending"
    assert metadata["clause_number"] == "Clause 5.1(a)"
    assert metadata["citation_confidence"] >= 0.9
    assert metadata["citation_incomplete_reasons"] == []
    assert citation_is_complete_for_policy(metadata)


def test_missing_clause_is_incomplete_for_policy_documents():
    metadata = build_citation_metadata(
        page={"page_number": 7, "text": "Chapter 2: Customer Service\nComplaints must be escalated."},
        chunk_text="Complaints must be escalated.",
        document_type="policy",
    )

    assert metadata["pdf_page_number"] == 7
    assert metadata["document_heading"] == "Chapter 2: Customer Service"
    assert metadata["clause_number"] is None
    assert "missing_clause_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_chunk_without_clause_does_not_inherit_earlier_page_clause():
    page_text = """
    Chapter 5: SME Lending
    Clause 5.1(a) Secured SME DSR limit
    The DSR limit for secured SME loans is 60%.

    Clause 5.2 Collateral margin
    The borrower must maintain the approved collateral margin.
    Page 38
    """

    metadata = build_citation_metadata(
        page={"page_number": 42, "text": page_text},
        chunk_text="The borrower must maintain the approved collateral margin.",
        document_type="policy",
    )

    assert metadata["document_heading"] == "Chapter 5: SME Lending"
    assert metadata["printed_page_number"] == "38"
    assert metadata["clause_number"] is None
    assert "missing_clause_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_chunk_with_own_clause_uses_that_clause_on_multi_clause_page():
    page_text = """
    Chapter 5: SME Lending
    Clause 5.1(a) Secured SME DSR limit
    The DSR limit for secured SME loans is 60%.

    Clause 5.2 Collateral margin
    The borrower must maintain the approved collateral margin.
    Page 38
    """

    metadata = build_citation_metadata(
        page={"page_number": 42, "text": page_text},
        chunk_text="Clause 5.2 Collateral margin\nThe borrower must maintain the approved collateral margin.",
        document_type="policy",
    )

    assert metadata["clause_number"] == "Clause 5.2"
    assert metadata["citation_incomplete_reasons"] == []
    assert citation_is_complete_for_policy(metadata)


def test_section_heading_only_is_not_extracted_as_clause():
    metadata = build_citation_metadata(
        page={"page_number": 7, "text": "Section 2: Customer Service\nComplaints must be escalated."},
        chunk_text="Complaints must be escalated.",
        document_type="policy",
    )

    assert extract_clause_number("Section 2: Customer Service") is None
    assert metadata["document_heading"] == "Section 2: Customer Service"
    assert metadata["clause_number"] is None
    assert "missing_clause_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_article_heading_only_is_not_extracted_as_clause():
    metadata = build_citation_metadata(
        page={"page_number": 9, "text": "Article 3: Account Opening\nKYC documents are required."},
        chunk_text="KYC documents are required.",
        document_type="policy",
    )

    assert extract_clause_number("Article 3: Account Opening") is None
    assert metadata["document_heading"] == "Article 3: Account Opening"
    assert metadata["clause_number"] is None
    assert "missing_clause_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_empty_metadata_is_not_complete_for_policy_citation():
    assert not citation_is_complete_for_policy({})


def test_non_dict_metadata_is_not_complete_for_policy_citation():
    assert not citation_is_complete_for_policy(None)
    assert not citation_is_complete_for_policy("complete")


def test_whitespace_supplied_heading_and_clause_are_incomplete():
    metadata = build_citation_metadata(
        page={
            "page_number": 12,
            "document_heading": " \n\t ",
            "clause_number": "   ",
            "printed_page_number": " 38 ",
            "text": "Page 38",
        },
        chunk_text="",
        document_type="policy",
    )

    assert metadata["printed_page_number"] == "38"
    assert metadata["document_heading"] is None
    assert metadata["clause_number"] is None
    assert "missing_document_heading" in metadata["citation_incomplete_reasons"]
    assert "missing_clause_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_blank_string_pdf_page_number_is_incomplete():
    metadata = build_citation_metadata(
        page={
            "page_number": "   ",
            "document_heading": "Chapter 4: Credit Risk",
            "clause_number": "Clause 4.1",
        },
        chunk_text="",
        document_type="policy",
    )

    assert "missing_pdf_page_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_non_scalar_heading_and_clause_do_not_satisfy_completeness():
    metadata = build_citation_metadata(
        page={
            "page_number": 12,
            "document_heading": ["Chapter 4: Credit Risk"],
            "clause_number": {"number": "Clause 4.1"},
        },
        chunk_text="",
        document_type="policy",
    )

    assert metadata["document_heading"] is None
    assert metadata["clause_number"] is None
    assert "missing_document_heading" in metadata["citation_incomplete_reasons"]
    assert "missing_clause_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)
    assert not citation_is_complete_for_policy(
        {
            "pdf_page_number": 12,
            "document_heading": ["Chapter 4: Credit Risk"],
            "clause_number": {"number": "Clause 4.1"},
            "citation_incomplete_reasons": [],
        }
    )


def test_numeric_heading_and_clause_do_not_satisfy_completeness():
    metadata = build_citation_metadata(
        page={
            "page_number": 12,
            "document_heading": 123,
            "clause_number": 4.1,
        },
        chunk_text="",
        document_type="policy",
    )

    assert metadata["document_heading"] is None
    assert metadata["clause_number"] is None
    assert "missing_document_heading" in metadata["citation_incomplete_reasons"]
    assert "missing_clause_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_build_citation_metadata_fails_closed_for_missing_page():
    metadata = build_citation_metadata(page=None, chunk_text="", document_type="policy")

    assert metadata["pdf_page_number"] is None
    assert metadata["document_heading"] is None
    assert metadata["clause_number"] is None
    assert metadata["printed_page_number"] is None
    assert "missing_pdf_page_number" in metadata["citation_incomplete_reasons"]
    assert "missing_document_heading" in metadata["citation_incomplete_reasons"]
    assert "missing_clause_number" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_pdf_page_zero_counts_toward_citation_confidence():
    metadata = build_citation_metadata(
        page={"page_number": 0, "text": "Chapter 1: Scope\nClause 1 Applicability"},
        chunk_text="Clause 1 Applicability",
        document_type="policy",
    )

    assert metadata["pdf_page_number"] == 0
    assert metadata["citation_incomplete_reasons"] == []
    assert metadata["citation_confidence"] >= 0.9
    assert citation_is_complete_for_policy(metadata)


def test_extractors_return_none_for_empty_input():
    assert extract_document_heading(None) is None
    assert extract_document_heading("") is None
    assert extract_clause_number(None) is None
    assert extract_clause_number("") is None
    assert extract_printed_page_number(None) is None
    assert extract_printed_page_number("") is None


def test_section_sentence_is_extracted_as_clause():
    assert extract_clause_number("Section 12 requires annual board review.") == "Section 12"


def test_section_sentence_is_not_extracted_as_heading():
    assert extract_document_heading("Section 12 requires annual board review.") is None


def test_section_sentence_policy_citation_keeps_clause_but_requires_heading():
    metadata = build_citation_metadata(
        page={"page_number": 12, "text": "Section 12 requires annual board review."},
        chunk_text="",
        document_type="policy",
    )

    assert metadata["document_heading"] is None
    assert metadata["clause_number"] == "Section 12"
    assert "missing_document_heading" in metadata["citation_incomplete_reasons"]
    assert not citation_is_complete_for_policy(metadata)


def test_section_heading_without_punctuation_is_not_extracted_as_clause():
    text = "Section 2 Customer Service"

    assert extract_document_heading(text) == "Section 2 Customer Service"
    assert extract_clause_number(text) is None


def test_section_colon_sentence_is_extracted_as_clause_not_heading():
    text = "Section 12: The board must review credit exposures annually."

    assert extract_document_heading(text) is None
    assert extract_clause_number(text) == "Section 12"


def test_article_sentence_is_extracted_as_clause():
    assert extract_clause_number("Article 7 requires audit approval.") == "Article 7"


def test_article_sentence_is_not_extracted_as_heading():
    assert extract_document_heading("Article 7 requires audit approval.") is None


def test_article_heading_without_punctuation_is_not_extracted_as_clause():
    text = "Article 3 Account Opening"

    assert extract_document_heading(text) == "Article 3 Account Opening"
    assert extract_clause_number(text) is None


def test_article_dash_sentence_is_extracted_as_clause_not_heading():
    text = "Article 7 - The auditor shall approve exceptions."

    assert extract_document_heading(text) is None
    assert extract_clause_number(text) == "Article 7"


def test_nepali_printed_page_and_clause_are_extracted():
    text = "परिच्छेद ३: कर्जा नीति\nदफा ३.२ कर्जा नवीकरण\nपृष्ठ १२"

    assert extract_document_heading(text) == "परिच्छेद ३: कर्जा नीति"
    assert extract_clause_number(text) == "दफा ३.२"
    assert extract_printed_page_number(text) == "१२"
