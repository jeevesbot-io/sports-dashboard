/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        accent: {
          cyan: 'var(--sd-accent-cyan)',
          violet: 'var(--sd-accent-violet)',
        },
        surface: {
          0: 'var(--sd-surface-0)',
          50: 'var(--sd-surface-50)',
          100: 'var(--sd-surface-100)',
          200: 'var(--sd-surface-200)',
          300: 'var(--sd-surface-300)',
          400: 'var(--sd-surface-400)',
          500: 'var(--sd-surface-500)',
          600: 'var(--sd-surface-600)',
          700: 'var(--sd-surface-700)',
          800: 'var(--sd-surface-800)',
          900: 'var(--sd-surface-900)',
          950: 'var(--sd-surface-950)',
        },
        win: 'var(--sd-win)',
        draw: 'var(--sd-draw)',
        loss: 'var(--sd-loss)',
        newcastle: 'var(--sd-newcastle-gold)',
      },
      fontFamily: {
        display: ['Outfit', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'stat-xs': ['0.75rem', { lineHeight: '1' }],
        'stat-sm': ['0.875rem', { lineHeight: '1' }],
        'stat-md': ['1.25rem', { lineHeight: '1' }],
        'stat-lg': ['1.75rem', { lineHeight: '1' }],
        'stat-xl': ['2.25rem', { lineHeight: '1' }],
        'stat-2xl': ['3rem', { lineHeight: '1' }],
        'stat-3xl': ['4rem', { lineHeight: '1' }],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
        'shimmer': 'shimmer 1.5s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.12)',
        'glass-lg': '0 16px 48px rgba(0, 0, 0, 0.16)',
        'glass-glow': '0 0 24px rgba(6, 182, 212, 0.15)',
        'card-hover': '0 12px 40px rgba(0, 0, 0, 0.2)',
      },
      backdropBlur: {
        'glass': '20px',
      },
    },
  },
  corePlugins: {
    preflight: false,
  },
  plugins: [],
}
