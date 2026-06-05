import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import api from '../api/axios';
import { DEFAULT_FEATURE_FLAGS, FEATURE_METADATA } from '../config/featureFlags';
import { getCurrentUser } from '../config/rolePermissions';

const FeatureFlagContext = createContext({
  bankId: null,
  flags: DEFAULT_FEATURE_FLAGS,
  loading: false,
  error: '',
  isFeatureEnabled: () => false,
  refreshFeatureFlags: () => Promise.resolve(DEFAULT_FEATURE_FLAGS),
});

function flagsFromResponse(responseFeatures = []) {
  return responseFeatures.reduce(
    (nextFlags, feature) => ({
      ...nextFlags,
      [feature.feature_key]: Boolean(feature.enabled),
    }),
    { ...DEFAULT_FEATURE_FLAGS }
  );
}

export function FeatureFlagProvider({ children }) {
  const [bankId, setBankId] = useState(null);
  const [flags, setFlags] = useState(DEFAULT_FEATURE_FLAGS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const refreshFeatureFlags = useCallback(async () => {
    const currentUser = getCurrentUser();
    if (!currentUser) {
      setBankId(null);
      setFlags(DEFAULT_FEATURE_FLAGS);
      setError('');
      return DEFAULT_FEATURE_FLAGS;
    }

    setLoading(true);
    setError('');
    try {
      const response = await api.get('/feature-flags/effective');
      const nextFlags = flagsFromResponse(response.data?.features);
      setBankId(response.data?.bank_id || currentUser.bank_id || null);
      setFlags(nextFlags);
      return nextFlags;
    } catch (err) {
      setBankId(currentUser.bank_id || null);
      setFlags(DEFAULT_FEATURE_FLAGS);
      setError(err?.response?.data?.detail || 'Could not load feature controls.');
      return DEFAULT_FEATURE_FLAGS;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshFeatureFlags();
  }, [refreshFeatureFlags]);

  const isFeatureEnabled = useCallback((featureKey) => Boolean(flags[featureKey]), [flags]);

  const value = useMemo(
    () => ({
      bankId,
      flags,
      loading,
      error,
      isFeatureEnabled,
      refreshFeatureFlags,
    }),
    [bankId, flags, loading, error, isFeatureEnabled, refreshFeatureFlags]
  );

  return <FeatureFlagContext.Provider value={value}>{children}</FeatureFlagContext.Provider>;
}

export function FeatureUnavailable({ featureKey }) {
  const feature = FEATURE_METADATA[featureKey];
  return (
    <div className="p-xl max-w-container-max mx-auto">
      <section className="bg-white border border-slate-200 rounded-lg p-lg">
        <div className="w-11 h-11 rounded-lg bg-slate-100 flex items-center justify-center mb-md">
          <span className="material-symbols-outlined text-slate-500 text-[22px]">toggle_off</span>
        </div>
        <h1 className="text-h2 font-h2 text-on-surface">Feature unavailable</h1>
        <p className="text-body-md text-on-surface-variant mt-sm max-w-2xl">
          {feature?.label || 'This feature'} is currently turned off for this bank. Contact a Super Admin if employees need access.
        </p>
      </section>
    </div>
  );
}

export function FeatureGate({ featureKey, fallback = null, children }) {
  const { loading, isFeatureEnabled } = useFeatureFlags();
  if (loading) return fallback;
  return isFeatureEnabled(featureKey) ? children : fallback;
}

export function useFeatureFlags() {
  return useContext(FeatureFlagContext);
}
