export default function NotFoundState({ mode }) {
  return (
    <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
      <div className="flex items-center gap-2 font-semibold">
        <span className="material-symbols-outlined text-[18px]">search_off</span>
        Not found in approved sources
      </div>
      <p className="mt-1 text-amber-800">
        LipiCore did not find enough approved evidence for this request. Check document approval status, select the right uploaded file, or escalate to the responsible supervisor.
      </p>
      {mode && <p className="mt-2 text-xs font-semibold uppercase tracking-wide">Mode: {mode}</p>}
    </div>
  );
}
