import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api/axios';
import { getCurrentUser, ROLES } from '../config/rolePermissions';

const EMPTY_RATE = {
  currency_code: '',
  currency_name: '',
  unit: 1,
  buy_rate: '',
  sell_rate: '',
  middle_rate: '',
};

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.code === 'feature_disabled') return 'Market & Time is not enabled for this bank.';
  return fallback;
}

function formatDateTime(value, timezone) {
  if (!value) return 'Not published';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: timezone || undefined,
  }).format(new Date(value));
}

function formatClock(timezone) {
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: timezone || undefined,
  }).format(new Date());
}

export default function MarketAndTime() {
  const currentUser = getCurrentUser();
  const isAdmin = currentUser?.role === ROLES.SUPER_ADMIN || currentUser?.role === ROLES.BANK_ADMIN;
  const [summary, setSummary] = useState(null);
  const [clock, setClock] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({
    source_name: 'Bank Treasury',
    notes: '',
    rates: [{ ...EMPTY_RATE }],
  });

  const timezone = summary?.timezone || 'Asia/Kathmandu';
  const latestBatch = summary?.latest_rate_batch;
  const rates = latestBatch?.rates || [];

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setNotice('');
    try {
      const response = await api.get('/market-utilities/summary');
      setSummary(response.data);
      setClock(formatClock(response.data?.timezone || 'Asia/Kathmandu'));
    } catch (err) {
      setSummary(null);
      setNotice(messageFromError(err, 'Could not load market and time data.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  useEffect(() => {
    setClock(formatClock(timezone));
    const timer = window.setInterval(() => setClock(formatClock(timezone)), 1000);
    return () => window.clearInterval(timer);
  }, [timezone]);

  const businessDate = useMemo(() => {
    if (summary?.business_date) return summary.business_date;
    return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeZone: timezone }).format(new Date());
  }, [summary?.business_date, timezone]);

  const updateRate = (index, key, value) => {
    setForm((current) => ({
      ...current,
      rates: current.rates.map((rate, rateIndex) => (
        rateIndex === index ? { ...rate, [key]: value } : rate
      )),
    }));
  };

  const addRateRow = () => {
    setForm((current) => ({ ...current, rates: [...current.rates, { ...EMPTY_RATE }] }));
  };

  const removeRateRow = (index) => {
    setForm((current) => ({
      ...current,
      rates: current.rates.length === 1 ? current.rates : current.rates.filter((_, rateIndex) => rateIndex !== index),
    }));
  };

  const publishRates = async (event) => {
    event.preventDefault();
    setSaving(true);
    setNotice('');
    try {
      const payload = {
        source_name: form.source_name.trim() || 'Bank Treasury',
        notes: form.notes.trim() || null,
        rates: form.rates.map((rate) => ({
          currency_code: rate.currency_code.trim().toUpperCase(),
          currency_name: rate.currency_name.trim(),
          unit: Number(rate.unit) || 1,
          buy_rate: Number(rate.buy_rate),
          sell_rate: Number(rate.sell_rate),
          middle_rate: rate.middle_rate === '' ? null : Number(rate.middle_rate),
        })),
      };
      await api.post('/market-utilities/rate-batches', payload);
      setForm({ source_name: 'Bank Treasury', notes: '', rates: [{ ...EMPTY_RATE }] });
      await fetchSummary();
      setNotice('Exchange rates published.');
    } catch (err) {
      setNotice(messageFromError(err, 'Could not publish exchange rates.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg flex flex-col gap-md xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface">Market & Time</h1>
          <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">
            Bank-published exchange rates, local business date, and operational time reference.
          </p>
        </div>
        <button
          type="button"
          onClick={fetchSummary}
          disabled={loading}
          className="inline-flex items-center justify-center gap-xs rounded-lg border border-slate-300 px-md py-sm font-label-caps text-label-caps text-on-surface transition-colors hover:bg-white disabled:opacity-50"
        >
          <span className="material-symbols-outlined text-[17px]">refresh</span>
          Refresh
        </button>
      </header>

      {notice && (
        <div className="mb-md rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-slate-700">
          {notice}
        </div>
      )}

      <section className="mb-lg grid grid-cols-1 gap-gutter lg:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Local Time</p>
          <p className="mt-xs font-public-sans text-[28px] font-black text-on-surface">{clock || 'Loading'}</p>
          <p className="text-body-sm text-on-surface-variant">{timezone}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Business Date</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{businessDate}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Rate Batch</p>
          <p className="mt-xs text-body-md font-bold text-on-surface">
            {latestBatch ? formatDateTime(latestBatch.published_at, timezone) : 'No rates published'}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Update Policy</p>
          <p className="mt-xs text-body-sm font-semibold text-on-surface">
            {summary?.rate_update_policy || 'Bank-published rates; expected 2-3 updates daily.'}
          </p>
        </div>
      </section>

      <section className="mb-lg rounded-lg border border-slate-200 bg-white">
        <div className="flex flex-col gap-xs border-b border-slate-100 px-lg py-md sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-h2 font-h2 text-on-surface">Exchange Rates</h2>
            <p className="text-body-sm text-on-surface-variant">
              {latestBatch ? `${latestBatch.source_name}${latestBatch.notes ? ` - ${latestBatch.notes}` : ''}` : 'No bank-published batch available.'}
            </p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left">
            <thead>
              <tr className="border-b border-slate-100 text-[11px] font-bold uppercase text-slate-400">
                <th className="px-lg py-sm">Currency</th>
                <th className="px-lg py-sm">Unit</th>
                <th className="px-lg py-sm">Buy</th>
                <th className="px-lg py-sm">Sell</th>
                <th className="px-lg py-sm">Middle</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rates.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-lg py-xl text-center text-body-sm text-on-surface-variant">
                    No rates published yet.
                  </td>
                </tr>
              ) : rates.map((rate) => (
                <tr key={rate.id}>
                  <td className="px-lg py-md">
                    <p className="font-bold text-on-surface">{rate.currency_code}</p>
                    <p className="text-body-sm text-on-surface-variant">{rate.currency_name}</p>
                  </td>
                  <td className="px-lg py-md text-body-sm text-on-surface">{rate.unit}</td>
                  <td className="px-lg py-md text-body-sm font-semibold text-on-surface">{rate.buy_rate.toFixed(4)}</td>
                  <td className="px-lg py-md text-body-sm font-semibold text-on-surface">{rate.sell_rate.toFixed(4)}</td>
                  <td className="px-lg py-md text-body-sm text-on-surface-variant">
                    {rate.middle_rate == null ? '-' : rate.middle_rate.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {isAdmin && (
        <section className="rounded-lg border border-slate-200 bg-white p-lg">
          <div className="mb-md">
            <h2 className="text-h2 font-h2 text-on-surface">Publish Rate Batch</h2>
            <p className="text-body-sm text-on-surface-variant">Saved batches are bank-scoped and visible to enabled employees.</p>
          </div>

          <form onSubmit={publishRates} className="space-y-md">
            <div className="grid grid-cols-1 gap-md lg:grid-cols-2">
              <div>
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Source</label>
                <input
                  value={form.source_name}
                  onChange={(event) => setForm((current) => ({ ...current, source_name: event.target.value }))}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Notes</label>
                <input
                  value={form.notes}
                  onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-sm">
              {form.rates.map((rate, index) => (
                <div key={index} className="grid grid-cols-1 gap-sm rounded-lg border border-slate-100 bg-slate-50 p-sm lg:grid-cols-[1fr_1.5fr_90px_1fr_1fr_1fr_auto]">
                  <input
                    value={rate.currency_code}
                    onChange={(event) => updateRate(index, 'currency_code', event.target.value)}
                    placeholder="USD"
                    className="rounded border border-slate-200 bg-white px-sm py-sm text-body-sm focus:border-secondary focus:outline-none"
                    required
                  />
                  <input
                    value={rate.currency_name}
                    onChange={(event) => updateRate(index, 'currency_name', event.target.value)}
                    placeholder="US Dollar"
                    className="rounded border border-slate-200 bg-white px-sm py-sm text-body-sm focus:border-secondary focus:outline-none"
                    required
                  />
                  <input
                    type="number"
                    min="1"
                    value={rate.unit}
                    onChange={(event) => updateRate(index, 'unit', event.target.value)}
                    className="rounded border border-slate-200 bg-white px-sm py-sm text-body-sm focus:border-secondary focus:outline-none"
                    required
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={rate.buy_rate}
                    onChange={(event) => updateRate(index, 'buy_rate', event.target.value)}
                    placeholder="Buy"
                    className="rounded border border-slate-200 bg-white px-sm py-sm text-body-sm focus:border-secondary focus:outline-none"
                    required
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={rate.sell_rate}
                    onChange={(event) => updateRate(index, 'sell_rate', event.target.value)}
                    placeholder="Sell"
                    className="rounded border border-slate-200 bg-white px-sm py-sm text-body-sm focus:border-secondary focus:outline-none"
                    required
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={rate.middle_rate}
                    onChange={(event) => updateRate(index, 'middle_rate', event.target.value)}
                    placeholder="Middle"
                    className="rounded border border-slate-200 bg-white px-sm py-sm text-body-sm focus:border-secondary focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => removeRateRow(index)}
                    className="inline-flex items-center justify-center rounded border border-slate-200 bg-white px-sm py-sm text-slate-500 hover:text-slate-900"
                    aria-label="Remove rate row"
                  >
                    <span className="material-symbols-outlined text-[18px]">delete</span>
                  </button>
                </div>
              ))}
            </div>

            <div className="flex flex-col gap-sm sm:flex-row sm:items-center sm:justify-between">
              <button
                type="button"
                onClick={addRateRow}
                className="inline-flex items-center justify-center gap-xs rounded-lg border border-slate-300 px-md py-sm font-label-caps text-label-caps text-on-surface hover:bg-slate-50"
              >
                <span className="material-symbols-outlined text-[17px]">add</span>
                Add Currency
              </button>
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center justify-center gap-xs rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90 disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[17px]">publish</span>
                {saving ? 'Publishing...' : 'Publish Rates'}
              </button>
            </div>
          </form>
        </section>
      )}
    </div>
  );
}
