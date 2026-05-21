/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Financial Enterprise AI design tokens
        'primary':                  'var(--brand-primary)',
        'on-primary':               '#ffffff',
        'primary-container':        'var(--brand-primary)',
        'on-primary-container':     '#7c839b',
        'primary-fixed':            '#dae2fd',
        'primary-fixed-dim':        '#bec6e0',
        'on-primary-fixed':         '#131b2e',
        'on-primary-fixed-variant': '#3f465c',
        'inverse-primary':          '#bec6e0',

        'secondary':                'var(--brand-accent)',
        'on-secondary':             '#ffffff',
        'secondary-container':      '#316bf3',
        'on-secondary-container':   '#fefcff',
        'secondary-fixed':          '#dbe1ff',
        'secondary-fixed-dim':      '#b4c5ff',
        'on-secondary-fixed':       '#00174b',
        'on-secondary-fixed-variant': '#003ea8',

        'tertiary':                 '#000000',
        'on-tertiary':              '#ffffff',
        'tertiary-container':       '#002113',
        'on-tertiary-container':    '#009668',
        'tertiary-fixed':           '#6ffbbe',
        'tertiary-fixed-dim':       '#4edea3',
        'on-tertiary-fixed':        '#002113',
        'on-tertiary-fixed-variant': '#005236',

        'error':                    '#ba1a1a',
        'on-error':                 '#ffffff',
        'error-container':          '#ffdad6',
        'on-error-container':       '#93000a',

        'surface':                  '#f8f9ff',
        'surface-dim':              '#cbdbf5',
        'surface-bright':           '#f8f9ff',
        'surface-container-lowest': '#ffffff',
        'surface-container-low':    '#eff4ff',
        'surface-container':        '#e5eeff',
        'surface-container-high':   '#dce9ff',
        'surface-container-highest':'#d3e4fe',
        'surface-tint':             '#565e74',
        'surface-variant':          '#d3e4fe',

        'on-surface':               '#0b1c30',
        'on-surface-variant':       '#45464d',
        'inverse-surface':          '#213145',
        'inverse-on-surface':       '#eaf1ff',

        'outline':                  '#76777d',
        'outline-variant':          '#c6c6cd',

        'background':               '#f8f9ff',
        'on-background':            '#0b1c30',
      },
      borderRadius: {
        DEFAULT: '0.125rem',   // 2px — standard sharp elements
        'lg':    '0.25rem',    // 4px — large containers
        'xl':    '0.5rem',     // 8px — prominent cards
        'full':  '9999px',     // pills/chips
      },
      spacing: {
        'unit':          '4px',
        'xs':            '4px',
        'sm':            '8px',
        'md':            '16px',
        'lg':            '24px',
        'xl':            '48px',
        'gutter':        '24px',
        'container-max': '1440px',
      },
      fontFamily: {
        'public-sans': ['"Public Sans"', 'sans-serif'],
        'inter':       ['Inter', 'sans-serif'],
        'h1':          ['"Public Sans"', 'sans-serif'],
        'h2':          ['"Public Sans"', 'sans-serif'],
        'body-lg':     ['Inter', 'sans-serif'],
        'body-md':     ['Inter', 'sans-serif'],
        'body-sm':     ['Inter', 'sans-serif'],
        'label-caps':  ['Inter', 'sans-serif'],
        'nepali-supplement': ['Inter', 'sans-serif'],
      },
      fontSize: {
        'h1':          ['36px', { lineHeight: '1.2', letterSpacing: '0', fontWeight: '700' }],
        'h2':          ['24px', { lineHeight: '1.3', letterSpacing: '0', fontWeight: '600' }],
        'body-lg':     ['18px', { lineHeight: '1.6', fontWeight: '400' }],
        'body-md':     ['16px', { lineHeight: '1.5', fontWeight: '400' }],
        'body-sm':     ['14px', { lineHeight: '1.5', fontWeight: '400' }],
        'label-caps':  ['12px', { lineHeight: '1', letterSpacing: '0.05em', fontWeight: '600' }],
        'nepali-supplement': ['110%', { lineHeight: '1.8' }],
      },
      boxShadow: {
        'card':     '0px 1px 3px rgba(15, 23, 42, 0.06)',
        'floating': '0px 4px 12px rgba(15, 23, 42, 0.08)',
        'panel':    '0px 8px 24px rgba(15, 23, 42, 0.10)',
      },
      keyframes: {
        'blink': {
          '0%, 100%': { opacity: '0.2' },
          '20%':      { opacity: '1' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.5' },
        },
        'slide-in': {
          '0%':   { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)',    opacity: '1' },
        },
        'fade-in': {
          '0%':   { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'blink':       'blink 1.4s infinite both',
        'pulse-soft':  'pulse-soft 2s ease-in-out infinite',
        'slide-in':    'slide-in 0.2s ease-out',
        'fade-in':     'fade-in 0.15s ease-out',
      },
    },
  },
  plugins: [],
}
