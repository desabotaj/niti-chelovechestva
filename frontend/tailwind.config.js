/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        cosmos: {
          950: '#020617',
          900: '#0a0e2a',
          800: '#11163d',
          700: '#1a1d35',
          600: '#252a4f',
        },
        thread: {
          50:  '#fff7e6',
          100: '#ffe8b3',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          700: '#b45309',
        },
        flow: {
          cyan: '#22d3ee',
          violet: '#c084fc',
          rose: '#fb7185',
        },
      },
      keyframes: {
        slowSpin: {
          '0%':   { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        slowPulse: {
          '0%, 100%': { opacity: '0.6' },
          '50%':      { opacity: '1' },
        },
        rise: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'slow-spin': 'slowSpin 120s linear infinite',
        'slow-pulse': 'slowPulse 4s ease-in-out infinite',
        'rise': 'rise 0.6s ease-out both',
      },
    },
  },
  plugins: [],
}
