import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import api from '../api/axios';

const DEFAULT_BRANDING = {
  product_name: 'BankAi',
  bank_name: 'Your Bank',
  logo_url: null,
  primary_color: '#17324d',
  accent_color: '#c7902c',
  welcome_message: 'Ask approved bank knowledge, analyze internal files, and draft staff-ready answers.',
  support_contact: null,
  disclaimer: 'Internal staff use only. Verify critical outputs against approved source documents.',
  allowed_modes: ['ask_knowledge', 'analyze_file', 'summarize', 'draft', 'translate', 'compare'],
};

const BrandingContext = createContext(DEFAULT_BRANDING);

function applyBrandingToDocument(branding) {
  document.documentElement.style.setProperty('--brand-primary', branding.primary_color || DEFAULT_BRANDING.primary_color);
  document.documentElement.style.setProperty('--brand-accent', branding.accent_color || DEFAULT_BRANDING.accent_color);
  document.title = `${branding.product_name || DEFAULT_BRANDING.product_name} | ${branding.bank_name || DEFAULT_BRANDING.bank_name}`;
}

export function BrandingProvider({ children }) {
  const [branding, setBranding] = useState(DEFAULT_BRANDING);

  useEffect(() => {
    let mounted = true;

    api.get('/config/branding')
      .then((response) => {
        if (!mounted) return;
        setBranding({ ...DEFAULT_BRANDING, ...response.data });
      })
      .catch(() => {
        if (mounted) setBranding(DEFAULT_BRANDING);
      });

    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    applyBrandingToDocument(branding);
  }, [branding]);

  const value = useMemo(() => ({ ...branding, setBranding }), [branding]);
  return <BrandingContext.Provider value={value}>{children}</BrandingContext.Provider>;
}

export function useBranding() {
  return useContext(BrandingContext);
}
