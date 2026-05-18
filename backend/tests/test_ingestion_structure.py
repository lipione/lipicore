from app.services.ingestion_service import build_indexable_chunks


def test_build_indexable_chunks_preserves_page_and_section_metadata():
    pages = [
        {
            "page_number": 1,
            "text": "Section 1 Introduction\nThis policy explains account opening responsibilities.",
        },
        {
            "page_number": 2,
            "text": "Section 2 KYC Review\nBranch staff must verify KYC documents before account opening.",
        },
    ]

    chunks = build_indexable_chunks(pages, chunk_size=120, chunk_overlap=20)

    assert chunks[0]["page_number"] == 1
    assert chunks[0]["section_label"] == "Section 1"
    assert chunks[0]["text"].startswith("Section 1 Introduction")
    assert chunks[1]["page_number"] == 2
    assert chunks[1]["section_label"] == "Section 2"
    assert "verify KYC" in chunks[1]["text"]


def test_build_indexable_chunks_falls_back_to_document_level_text():
    chunks = build_indexable_chunks(
        [{"page_number": None, "text": "Clause 3.1 requires supervisor approval for exceptions."}],
        chunk_size=120,
        chunk_overlap=20,
    )

    assert chunks == [
        {
            "text": "Clause 3.1 requires supervisor approval for exceptions.",
            "page_number": None,
            "section_label": "Clause 3.1",
        }
    ]
