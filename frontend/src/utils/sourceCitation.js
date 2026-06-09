export function hasCitationValue(value) {
  return value !== null && value !== undefined && value !== '';
}

export function firstCitationValue(...values) {
  return values.find(hasCitationValue);
}

export function sourcePdfPage(source) {
  return firstCitationValue(source?.pdf_page_number, source?.page_number) ?? null;
}

export function sourceTitle(source) {
  return source?.document_title || source?.title || source?.file_name || 'Source';
}

export function sourceLocationParts(source) {
  const pdfPage = sourcePdfPage(source);
  const parts = [];
  if (source?.document_heading) parts.push(`Heading: ${source.document_heading}`);
  if (source?.clause_number) parts.push(`Clause: ${source.clause_number}`);
  if (!source?.document_heading && (source?.section_label || source?.section_number)) {
    parts.push(`Section: ${source.section_label || source.section_number}`);
  }
  if (hasCitationValue(pdfPage)) parts.push(`PDF p.${pdfPage}`);
  if (hasCitationValue(source?.printed_page_number)) parts.push(`Printed p.${source.printed_page_number}`);
  if (!parts.length && Number.isInteger(source?.chunk_index)) parts.push(`Chunk ${source.chunk_index + 1}`);
  return parts;
}

export function sourceLocationLabel(source) {
  return sourceLocationParts(source).join(' · ');
}

export function formatSourceCitation(source) {
  const parts = [sourceTitle(source), ...sourceLocationParts(source)];
  if (source?.source_status) parts.push(`Status: ${source.source_status}`);
  else if (source?.document_status || source?.version_state) {
    parts.push(`Status: ${[source.document_status, source.version_state].filter(Boolean).join('/')}`);
  }
  if (source?.regulator) parts.push(`Regulator: ${source.regulator}`);
  if (source?.jurisdiction) parts.push(`Jurisdiction: ${source.jurisdiction}`);
  if (hasCitationValue(source?.document_id)) parts.push(`Doc ID: ${source.document_id}`);
  return parts.filter(Boolean).join(' | ');
}

export function confidenceLabel(value) {
  if (value === null || value === undefined || value === '') return null;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  return `${Math.round(Math.max(0, Math.min(numeric, 1)) * 100)}%`;
}

export function sourceHasIncompleteCitation(source) {
  return source?.citation_verification === 'citation_incomplete'
    || source?.citation_complete === false
    || (Array.isArray(source?.citation_incomplete_reasons) && source.citation_incomplete_reasons.length > 0);
}

export function citationVerificationStatusFromSources(sources = []) {
  if (sources.some(sourceHasIncompleteCitation)) return 'citation_incomplete';
  return sources.find(source => source?.citation_verification)?.citation_verification || null;
}

export function trustLabelFromCitationStatus(status, sourceCount = 0) {
  if (status === 'citation_incomplete') return 'citation_incomplete';
  if (status === 'supported') return 'source_supported';
  if (status === 'partially_supported') return 'partially_source_supported';
  if (status === 'unsupported') return 'not_source_supported';
  return sourceCount > 0 ? 'source_unverified' : 'no_sources';
}

export function answerMetadataFromSources(sources = [], mode = 'ask_knowledge') {
  const sourceCount = sources.length;
  if (sourceCount === 0) return null;
  const citationStatus = citationVerificationStatusFromSources(sources);
  const hasIncompleteCitation = citationStatus === 'citation_incomplete';

  return {
    mode,
    answer_type: hasIncompleteCitation ? 'citation_incomplete' : 'official_source_backed',
    source_count: sourceCount,
    requires_sources: true,
    trust_label: trustLabelFromCitationStatus(citationStatus, sourceCount),
    citation_verification: {
      status: citationStatus || 'no_sources',
    },
  };
}
