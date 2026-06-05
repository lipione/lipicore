import { useEffect, useMemo, useState } from 'react';
import api from '../api/axios';
import { DEFAULT_FEATURE_FLAGS, FEATURE_GROUPS } from '../config/featureFlags';
import { getCurrentUser, ROLES } from '../config/rolePermissions';
import { useFeatureFlags } from '../contexts/FeatureFlagContext';

function ToggleSwitch({ checked, disabled, onChange }) {
  return (
    <button
      type="button"
      disabled={disabled}
      aria-pressed={checked}
      onClick={onChange}
      className={`relative h-7 w-12 rounded-full transition-colors flex-shrink-0 disabled:cursor-not-allowed disabled:opacity-60 ${
        checked ? 'bg-secondary' : 'bg-slate-300'
      }`}
    >
      <span
        className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow transition-all ${
          checked ? 'left-6' : 'left-1'
        }`}
      />
    </button>
  );
}

function normalizeFlags(features = []) {
  return features.reduce(
    (nextFlags, feature) => ({
      ...nextFlags,
      [feature.feature_key]: feature,
    }),
    Object.keys(DEFAULT_FEATURE_FLAGS).reduce((defaults, key) => ({
      ...defaults,
      [key]: {
        feature_key: key,
        enabled: DEFAULT_FEATURE_FLAGS[key],
        reason: '',
        updated_at: null,
      },
    }), {})
  );
}

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.message) return detail.message;
  return fallback;
}

export default function SuperAdminFeatureControls() {
  const currentUser = getCurrentUser();
  const { bankId: effectiveBankId, refreshFeatureFlags } = useFeatureFlags();
  const [banks, setBanks] = useState([]);
  const [selectedBankId, setSelectedBankId] = useState(currentUser?.bank_id || '');
  const [flagsByKey, setFlagsByKey] = useState(() => normalizeFlags());
  const [reasonByKey, setReasonByKey] = useState({});
  const [loadingBanks, setLoadingBanks] = useState(true);
  const [loadingFlags, setLoadingFlags] = useState(false);
  const [savingKey, setSavingKey] = useState('');
  const [notice, setNotice] = useState('');

  const isSuperAdmin = currentUser?.role === ROLES.SUPER_ADMIN;

  useEffect(() => {
    if (!isSuperAdmin) return;
    let mounted = true;

    async function fetchBanks() {
      setLoadingBanks(true);
      setNotice('');
      try {
        const response = await api.get('/banks');
        if (!mounted) return;
        const bankList = Array.isArray(response.data) ? response.data : [];
        setBanks(bankList);
        if (bankList.length > 0) {
          setSelectedBankId((current) => current || bankList[0].id);
        }
      } catch (err) {
        if (mounted) {
          setBanks([]);
          setNotice(messageFromError(err, 'Could not load banks for feature management.'));
        }
      } finally {
        if (mounted) setLoadingBanks(false);
      }
    }

    fetchBanks();
    return () => { mounted = false; };
  }, [isSuperAdmin]);

  useEffect(() => {
    if (!isSuperAdmin || !selectedBankId) return;
    let mounted = true;

    async function fetchFlags() {
      setLoadingFlags(true);
      setNotice('');
      try {
        const response = await api.get('/feature-flags', {
          params: { bank_id: selectedBankId },
        });
        if (!mounted) return;
        setFlagsByKey(normalizeFlags(response.data?.features));
      } catch (err) {
        if (mounted) {
          setFlagsByKey(normalizeFlags());
          setNotice(messageFromError(err, 'Could not load feature controls for this bank.'));
        }
      } finally {
        if (mounted) setLoadingFlags(false);
      }
    }

    fetchFlags();
    return () => { mounted = false; };
  }, [isSuperAdmin, selectedBankId]);

  const enabledCount = useMemo(
    () => Object.values(flagsByKey).filter((flag) => flag.enabled).length,
    [flagsByKey]
  );

  const featureCount = Object.keys(DEFAULT_FEATURE_FLAGS).length;
  const selectedBank = banks.find((bank) => String(bank.id) === String(selectedBankId));

  const handleToggle = async (featureKey) => {
    if (!selectedBankId) return;
    const currentFlag = flagsByKey[featureKey];
    const enabled = !currentFlag?.enabled;
    const reason = reasonByKey[featureKey]?.trim()
      || `${enabled ? 'Enabled' : 'Disabled'} from Super Admin feature controls`;

    setSavingKey(featureKey);
    setNotice('');
    try {
      const response = await api.patch(`/feature-flags/${selectedBankId}/${featureKey}`, {
        enabled,
        reason,
      });
      setFlagsByKey((current) => ({
        ...current,
        [featureKey]: response.data,
      }));
      setReasonByKey((current) => ({ ...current, [featureKey]: '' }));
      if (String(effectiveBankId) === String(selectedBankId)) {
        await refreshFeatureFlags();
      }
      setNotice(`${response.data.enabled ? 'Enabled' : 'Disabled'} ${featureKey.replaceAll('_', ' ')} for ${selectedBank?.name || 'selected bank'}.`);
    } catch (err) {
      setNotice(messageFromError(err, 'Could not update this feature flag.'));
    } finally {
      setSavingKey('');
    }
  };

  if (!isSuperAdmin) {
    return (
      <div className="p-xl max-w-container-max mx-auto">
        <section className="bg-white border border-slate-200 rounded-lg p-lg">
          <div className="w-11 h-11 rounded-lg bg-slate-100 flex items-center justify-center mb-md">
            <span className="material-symbols-outlined text-slate-500 text-[22px]">lock</span>
          </div>
          <h1 className="text-h2 font-h2 text-on-surface">Restricted feature controls</h1>
          <p className="text-body-md text-on-surface-variant mt-sm">
            Only Super Admin users can enable or disable employee workspace features.
          </p>
        </section>
      </div>
    );
  }

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg flex flex-col gap-md xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface">Feature Controls</h1>
          <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">
            Turn employee banking modules on or off per bank. Disabled modules stay hidden in navigation, and backend services can enforce the same bank-level flag.
          </p>
        </div>
        <div className="flex flex-col gap-sm sm:flex-row sm:items-center">
          <label className="font-label-caps text-label-caps text-on-surface-variant uppercase">Bank</label>
          <select
            value={selectedBankId}
            disabled={loadingBanks}
            onChange={(event) => setSelectedBankId(event.target.value)}
            className="min-w-64 rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
          >
            {!banks.length && <option value="">No banks available</option>}
            {banks.map((bank) => (
              <option key={bank.id} value={bank.id}>{bank.name} ({bank.code})</option>
            ))}
          </select>
        </div>
      </header>

      {notice && (
        <div className="mb-md rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-slate-700">
          {notice}
        </div>
      )}

      <section className="mb-lg grid grid-cols-1 gap-gutter lg:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Selected Bank</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{selectedBank?.name || 'Select a bank'}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Enabled Features</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{enabledCount} / {featureCount}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Rate Update Policy</p>
          <p className="mt-xs text-body-md font-semibold text-on-surface">Bank controlled, 2-3 updates daily</p>
        </div>
      </section>

      <div className="space-y-lg">
        {FEATURE_GROUPS.map((group) => (
          <section key={group.label} className="rounded-lg border border-slate-200 bg-white p-lg">
            <div className="mb-md flex items-center justify-between gap-md border-b border-slate-100 pb-md">
              <div>
                <h2 className="text-h2 font-h2 text-on-surface">{group.label}</h2>
                <p className="text-body-sm text-on-surface-variant">
                  {group.features.filter((feature) => flagsByKey[feature.key]?.enabled).length} of {group.features.length} enabled
                </p>
              </div>
            </div>

            <div className="divide-y divide-slate-100">
              {group.features.map((feature) => {
                const flag = flagsByKey[feature.key] || {};
                const enabled = Boolean(flag.enabled);
                const busy = savingKey === feature.key || loadingFlags;
                return (
                  <div key={feature.key} className="grid grid-cols-1 gap-md py-md xl:grid-cols-[1fr_320px_auto] xl:items-center">
                    <div className="flex min-w-0 items-start gap-md">
                      <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg ${
                        enabled ? 'bg-tertiary-fixed-dim text-on-tertiary-container' : 'bg-slate-100 text-slate-500'
                      }`}>
                        <span className="material-symbols-outlined text-[21px]">{feature.icon}</span>
                      </div>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-sm">
                          <h3 className="text-body-md font-bold text-on-surface">{feature.label}</h3>
                          <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                            enabled ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {enabled ? 'On' : 'Off'}
                          </span>
                        </div>
                        <p className="mt-xs text-body-sm text-on-surface-variant">{feature.desc}</p>
                        {flag.updated_at && (
                          <p className="mt-xs text-[11px] font-medium uppercase text-slate-400">
                            Updated {new Date(flag.updated_at).toLocaleString()}
                          </p>
                        )}
                      </div>
                    </div>

                    <input
                      value={reasonByKey[feature.key] || ''}
                      onChange={(event) => setReasonByKey((current) => ({ ...current, [feature.key]: event.target.value }))}
                      placeholder="Reason for audit log"
                      className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                    />

                    <div className="flex items-center justify-between gap-md xl:justify-end">
                      <span className="text-body-sm font-semibold text-on-surface-variant xl:hidden">
                        {enabled ? 'Enabled' : 'Disabled'}
                      </span>
                      <ToggleSwitch checked={enabled} disabled={busy || !selectedBankId} onChange={() => handleToggle(feature.key)} />
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
