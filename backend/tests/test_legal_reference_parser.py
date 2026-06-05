from app.services.legal_reference_parser import LegalHierarchy, legal_hierarchy_path, parse_legal_hierarchy


def test_parse_legal_hierarchy_extracts_nepali_parts_and_clauses():
    text = """
    नेपाल बैंक अधिनियम
    भाग २
    अध्याय ५: ऋण नियम
    दफा ३.१: सावधानीपूर्वक निरीक्षण
    १२१.१ विवरण
    """

    hierarchy = parse_legal_hierarchy(text)

    assert hierarchy.document_title == "नेपाल बैंक अधिनियम"
    assert hierarchy.part == "भाग २"
    assert hierarchy.chapter == "अध्याय ५: ऋण नियम"
    assert hierarchy.clause == "दफा 3.1: सावधानीपूर्वक निरीक्षण"
    assert legal_hierarchy_path(hierarchy=hierarchy) == "नेपाल बैंक अधिनियम / भाग २ / अध्याय ५: ऋण नियम"


def test_parse_legal_hierarchy_prefers_section_clause_in_english_text():
    text = """
    Banking Conduct Manual
    Section 4: Customer Claims
    Clause 4.2: Escalation Timeline
    """

    hierarchy = parse_legal_hierarchy(text)

    assert hierarchy.document_title == "Banking Conduct Manual"
    assert hierarchy.section == "section 4: customer claims"
    assert hierarchy.clause == "clause 4.2: escalation timeline"


def test_legal_hierarchy_path_returns_none_for_unmatched_text():
    assert legal_hierarchy_path(hierarchy=LegalHierarchy()) is None


def test_parse_legal_hierarchy_allows_chapter_without_part_or_section():
    hierarchy = parse_legal_hierarchy("Chapter 10: Escalation")

    assert hierarchy.document_title is None
    assert hierarchy.chapter == "chapter 10: escalation"
    assert hierarchy.section is None
    assert hierarchy.clause is None
    assert legal_hierarchy_path(hierarchy=hierarchy) == "chapter 10: escalation"
