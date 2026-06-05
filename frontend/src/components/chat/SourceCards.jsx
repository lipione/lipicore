import { hasCitationValue, sourcePdfPage } from '../../utils/sourceCitation';

export default function SourceCards({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-3 pt-3 border-t border-slate-100">
      <p className="font-label-caps text-[10px] text-slate-400 uppercase tracking-widest mb-2">Sources Used</p>
      <div className="flex flex-wrap gap-2">
        {sources.map((src, i) => {
          const pdfPage = sourcePdfPage(src);
          return (
            <span key={i} title={src.snippet}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white border border-slate-200 rounded text-[11px] font-medium text-slate-600 hover:border-secondary transition-colors cursor-default">
              <span className="material-symbols-outlined text-[13px] text-secondary">description</span>
              {src.document_title || src.title || 'Source'}
              {src.clause_number && <span className="text-slate-400 ml-0.5">[{src.clause_number}]</span>}
              {hasCitationValue(pdfPage) && <span className="text-slate-400 ml-0.5">[PDF p.{pdfPage}]</span>}
              {hasCitationValue(src.printed_page_number) && <span className="text-slate-400 ml-0.5">[printed p.{src.printed_page_number}]</span>}
            </span>
          );
        })}
      </div>
    </div>
  );
}
