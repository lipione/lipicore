function confidenceLabel(value) {
  if (value === null || value === undefined) return null;
  return `${Math.round(Number(value) * 100)}%`;
}

export default function SourceMetadataStrip({ source }) {
  const items = [
    source?.page_number ? `Page ${source.page_number}` : null,
    source?.section_label || source?.section_number || null,
    source?.chunk_index !== null && source?.chunk_index !== undefined ? `Chunk ${source.chunk_index}` : null,
    confidenceLabel(source?.ocr_confidence) ? `OCR ${confidenceLabel(source.ocr_confidence)}` : null,
    confidenceLabel(source?.table_confidence) ? `Table ${confidenceLabel(source.table_confidence)}` : null,
    source?.citation_verification ? `Citation ${source.citation_verification}` : null,
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
