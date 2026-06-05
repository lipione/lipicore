export function hasCitationValue(value) {
  return value !== null && value !== undefined && value !== '';
}

export function firstCitationValue(...values) {
  return values.find(hasCitationValue);
}

export function sourcePdfPage(source) {
  return firstCitationValue(source?.pdf_page_number, source?.page_number) ?? null;
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
