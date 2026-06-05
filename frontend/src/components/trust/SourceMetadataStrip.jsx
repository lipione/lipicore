import { confidenceLabel, firstCitationValue, hasCitationValue, sourcePdfPage } from '../../utils/sourceCitation';

export default function SourceMetadataStrip({ source }) {
  const pdfPage = sourcePdfPage(source);
  const sourceStatus = firstCitationValue(source?.source_status, source?.document_status);

  const items = [
    source?.document_heading ? `Heading: ${source.document_heading}` : null,
    source?.clause_number ? `Clause: ${source.clause_number}` : null,
    hasCitationValue(pdfPage) ? `PDF p.${pdfPage}` : null,
    hasCitationValue(source?.printed_page_number) ? `Printed p.${source.printed_page_number}` : null,
    sourceStatus ? `Status ${sourceStatus}` : null,
    source?.effective_from ? `Effective from ${source.effective_from.slice(0, 10)}` : null,
    source?.effective_to ? `Effective until ${source.effective_to.slice(0, 10)}` : null,
    source?.citation_complete === false ? 'Citation incomplete' : null,
    source?.citation_incomplete_reasons?.length ? source.citation_incomplete_reasons.join(', ') : null,
    confidenceLabel(source?.citation_confidence) ? `Citation ${confidenceLabel(source.citation_confidence)}` : null,
    confidenceLabel(source?.ocr_confidence) ? `OCR ${confidenceLabel(source.ocr_confidence)}` : null,
    confidenceLabel(source?.table_confidence) ? `Table ${confidenceLabel(source.table_confidence)}` : null,
    source?.citation_verification ? `Answer ${source.citation_verification}` : null,
  ].filter(Boolean);

  if (!items.length) return null;

  return (
    <div className="flex flex-wrap gap-2 text-xs text-slate-600">
      {items.map((item) => (
        <span key={item} className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5">
          {item}
        </span>
      ))}
    </div>
  );
}
